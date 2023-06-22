from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from tqdm import tqdm
import shelve
from typing import Union, List, Tuple
import requests
import markdown
import logging
import webbrowser
import argparse
import sys
import os
import appdirs

CPC_PLTF = "Amstrad CPC"
C64_PLTF = "Commodore 64"
BND_GRP = "253"
SHELVE_FNAME = "data.shelve"
OUTPUT = "report.html"

PROD_LAST_COMMENT = "prod_last_comment"
PLATFORM_KNOWN_PRODS = "platform_known_prod"


class ProductionComment(object):
    def __init__(self, elt):
        logging.debug(elt.text)
        self._content = elt.find_element(By.XPATH, 'div[@class="content"]').text
        self._vote = elt.find_element(By.XPATH, 'div[@class="foot"]/span').text
        self._from = elt.find_element(
                By.XPATH,
                'div[@class="foot"]//a[contains(@class, "user")]') \
            .text

    def __repr__(self) -> str:
        vote = self._vote if self._vote else "piggy"
        return "%s [%s]: %s" % (self._from, vote, self._content)

    def __eq__(self, __value: object) -> bool:
        return self._content == \
            __value._content and \
            self._vote == __value._vote and \
            self._from == __value._from


class Production(object):
    def __init__(self, driver, link: str):
        logging.debug(f"Extract {link}")
        driver.get(link)

        self._id = link.split("which=")[1]
        self._link = link
        self._name = driver.find_element(By.ID, "prod-title").text
        self._comments = [ProductionComment(comment)
                            for comment in
                                driver.find_elements(By.XPATH, '//div[contains(@class, "comment")]')]
        self._download_link = driver.find_element(By.ID, "mainDownloadLink").get_attribute("href")

    def id(self) -> str:
        return self._id

    def link(self) -> str:
        return self._link

    def dowload_link(self) -> str:
        return self._download_link

    def last_comment(self) -> Union[None, ProductionComment]:
        if self._comments:
            return self._comments[-1]
        else:
            return None


class Check(object):
    def __init__(self, prod):
        self._prod = prod


class AtLeastOneNewComment(Check):
    def __init__(self, prod):
        super().__init__(prod)

    def __str__(self) -> str:
        return f"[{self._prod._name}]({self._prod.link()}) " \
               f"has at least one new comment ({self._prod.last_comment()})."


class DownloadLinkDead(Check):
    def __init__(self, prod):
        super().__init__(prod)

    def __str__(self) -> str:
        return f"[{self._prod._name}]({self._prod.link()}) has a dead download link."


class NewProduction(Check):
    def __init__(self, prod):
        super().__init__(prod)

    def __str__(self) -> str:
        # TODO add type instead of prod word
        return f"[{self._prod._name}]({self._prod.link()}) is a new prod."


def check_prod(f, driver, link: str) -> List[Check]:
    """Check if there is a new comment for the given prod"""
    checks = []
    current = Production(driver, link)

    key = f"{PROD_LAST_COMMENT}/{current.id()}"

    # Check for new comments
    previous = f[key] if key in f else None

    if not previous or (current.last_comment() != previous):
        checks.append(AtLeastOneNewComment(current))

    f[key] = current.last_comment()

    # Check for dead links
    r = requests.head(current.dowload_link())
    if not r.status_code == 200:
        checks.append(DownloadLinkDead(current))

    return checks


def collect_prods_name_and_url(driver) -> List[Tuple[str, str]]:
    # BUG does not handle when there are several pages. I let other users do it
    prods = driver.find_elements(By.XPATH, '//span[@class="prod"]/a')
    prods = [(p.text, p.get_attribute("href")) for p in prods]
    return prods


def check_grp(f, driver, grp_id) -> Tuple[str, List[Check]]:
    """Check if the group has new comments.
    TODO handle new prods ?
    """
    # Go to the website
    driver.get(f"https://www.pouet.net/groups.php?which={grp_id}")

    # Get the production list
    prods = collect_prods_name_and_url(driver)
    group_name = driver.title.split(" ::")[0]

    # Browse them and get checks
    checks = []
    for _, prod_link in tqdm(prods, desc=f"Check {group_name} prods at {driver.current_url}"):
        checks.extend(check_prod(f, driver, prod_link))

    return group_name,  checks


def check_pltf(f, driver, pltf_id: str) -> List[Check]:
    driver.get(f"https://www.pouet.net/prodlist.php?platform[]={pltf_id}")
    prods = collect_prods_name_and_url(driver)

    checks = []
    for prod_name, prod_link in tqdm(prods, desc=f"Check {pltf_id} prods at {driver.current_url}"):

        key = f"{PLATFORM_KNOWN_PRODS}/{prod_link}"
        if key not in f:
            checks.append(NewProduction(Production(driver, prod_link)))
        f[key] = prod_name

    return checks


def build_markdown_report(plateforms_name: List[str], groups_id: List[str]) -> str:
    # fname = str(hash( "".join(plateforms_name) + "".join(groups_id))) + ".shelve" # the db fname depends on the arguments XXX not yet sure if it is appropriate
    fname = "previous.shelve"
    folder = appdirs.user_cache_dir("pouetspy", "benediction")
    os.makedirs(folder, exist_ok=True)
    fname = os.path.join(folder, fname)
    f = shelve.open(fname, 'c')

    for key in [PROD_LAST_COMMENT, PLATFORM_KNOWN_PRODS]:
        if key not in f:
            f[key] = {}

    report = ""

    options = Options()
    options.add_argument("-headless")
    with webdriver.Firefox(options=options) as driver:

        for platform_name in plateforms_name:
            report += f"# {platform_name} checks\n\n"
            checks = check_pltf(f, driver, platform_name)
            if checks:
                report += "You have few things to checks.\n\n"
                for check in checks:
                    report += " - " + str(check) + "\n"
            else:
                report += "Everything seems good.\n\n"

        for group_id in groups_id:
            group_name, checks = check_grp(f, driver, group_id)
            report += f"# {group_name} checks\n"

            if checks:
                report += "You have few things to checks.\n\n"
                for check in checks:
                    report += " - " + str(check) + "\n"
            else:
                report += "Everything seems good.\n\n"

        driver.close()

    f.sync()

    return report


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser(
                    prog=sys.argv[0],
                    description='Automatically browse pouet.net to collect the new productions of'
                                ' your platform of interest and the new comments for productions '
                                'of your groups of interest.\n Usefull when you do not browse'
                                ' pouet.net too much often.',
                    epilog='Still work in progress. Feel free to send improvement patches.')
    parser.add_argument(
        "-p", "--platform",
        nargs="*",
        default=[],
        help=f"Specify the name of the plateform for which you want to collect new prods"
             f" (for example {CPC_PLTF})",
    )
    parser.add_argument(
        "-g", "--group",
        nargs="*",
        default=[],
        help=f"Specify the id of the group for which you want to collect the new comments"
             f"(for example {BND_GRP} for Benediction)",
    )

    args = parser.parse_args()

    report = build_markdown_report(args.platform, args.group)

    # Generate the report
    html = markdown.markdown(report)
    with open(OUTPUT, "w", encoding="utf-8", errors="xmlcharrefreplace") as output_file:
        output_file.write(html)

    # Display it
    webbrowser.open_new_tab(OUTPUT)
