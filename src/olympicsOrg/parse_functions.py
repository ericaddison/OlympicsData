###################################################################
# Functions used for parsing pages in olympics.org
###################################################################

import re
import json
from bs4 import BeautifulSoup
from bs4 import Tag

###################################################################

# filter to find links for relative path sites
# that are NOT in a no-go list
nogoPaths = ['/news.*', '/.*ioc.*', '/photos.*','/.*olympic.*/?',
             '/documents.*','/videos.*','/host.*','/ajax.*',
             '/.*sport.*','/.*medal.*','/sponsors.*','/.*mascot.*',
             '/sustainability.*','/legal.*','/.*torch.*',
             '/.*athlete.*','/.*artist.*','/ethics.*','/fr.*',
             '/cooperation.*','/good-governance.*',
             '/fight-against-doping.*','/playfair.*','/hbi.*',
             '/sha.*','/broadcasters.*','/ticketing.*',
             '/licensing.*','/suppliers.*','/museum.*',
             '/code-of-ethics.*']
def find_relative_links(tag):
    if type(tag) != Tag:
        return False    
    if tag.name != "a":
        return False
    if not tag.has_attr('href'):
        return False
    if tag.has_attr("class") and tag['class'][0] == "btn":
        return False
    if not re.match(re.compile("^\/"),tag['href']):
        return False
    for nogo in nogoPaths:
        if re.match(re.compile(nogo),tag['href']):
            return False
    return True

###################################################################

# generic parser for any page
# all pages should be run through this one
# looks for all relative links, minus those in
# the exclusion list, determined by the find_relative_links
# filter function. Also checks against the 
# list linksToVisit and the set visited
def parse_page(soup):
    relativeLinks = soup.find_all(find_relative_links)
    newLinks = []
    for a in relativeLinks:
        newLinks.append(a['href'])
    return newLinks


# convert a name to a link
def name_to_link(name):
    return name.lower().strip().replace(" ","-").replace("/","-")   

###################################################################

# parse a page for rankings from a rankings table

def find_rankings_header(tag):
    if type(tag) != Tag:
        return False
    return tag.name == "h2" and (tag.string == "Ranking" or tag.string == "Final")


def parse_rankings(soup):
    rankHeader = soup.find(find_rankings_header)
    
    if not rankHeader:
        return
    
    parent = rankHeader.find_parent()
    table = parent.find_next_sibling("table")
    if (not table is None): 
        rows = table.find_all("tr")

        newRankings = []
        for row in rows:
            res = {}
            cols = row.find_all("td")
            if len(cols)==4:
                
                # get the olympics
                title = soup.find("title").string.strip()
                res['olympics'] = name_to_link(re.compile("^\D+\d{4}").findall(title)[0])
                res['event'] = name_to_link(re.split("^\D+\d{4}",title)[1].split("-")[0])
                res['sport'] = name_to_link(title.split("Olympic ")[-1])
                res['rank'] = cols[0].get_text().strip().replace(".","")
                res['result'] = cols[2].get_text().strip()
                res['notes'] = cols[3].get_text().strip()
                
                links = cols[1].find_all("a")
                for a in links:
                    if a['href'] == "":
                        res['athlete']= "team"
                        res['country'] = a.get_text().strip()
                    else:
                        res['athlete'] = a['href'].split("/")[-1]
                        res['country'] = a.find(itemprop="nationality").string
                    newRankings.append(res)
        return newRankings

###################################################################

# parse one athlete from an athlete page
def parse_athlete_page(soup):
    ath = {}
    ath['name'] = soup.find("title").string.split(" - ")[0].title().strip()
    
    # first get the nationality of this athlete
    profileTag = soup.find("div",class_="profile-row")
    ath['nationality'] = profileTag.find("span").get_text()

    # get the id card
    idcard = soup.find("section",class_=re.compile("id-card.*")) 
    idcardItems = idcard.find_all("li")
    ath['sport'] = []
    for a in idcardItems[0].find_all("a"):
        ath['sport'].append(a['href'].split("/")[-1].strip())
    ath['country'] = []
    for a in idcardItems[1].find_all("a"):
        ath['country'].append(a['href'].split("/")[-1].strip()) 
    ath['born'] = idcardItems[2].get_text().strip().split("\n")[-1]    
    ath['olympics'] = []
    for a in idcardItems[3].find_all("a"):
        ath['olympics'].append(a['href'].split("/")[-1].strip())
    
    return ath

# filter function used to find the Results header
def find_results_header(tag):
    if type(tag) != Tag:
        return False
    return tag.name == "h2" and tag.string == "Results"


# parse results from an athlete page
# input: soup from an athlete page
# output: array of new results
def parse_results(soup):
    resHeader = soup.find(find_results_header)
    if not resHeader:
        return
    results = []

    resultRows = soup.find_all("div",class_="row")

    #print res
    for row in resultRows:
        newRes = {}
        res = row.find_all("span")
        newRes['medal'] = ""
        newRes['result'] = ""
        for item in res:
            if item.string in ['G', 'S', 'B']:
                newRes['medal'] = item.string
            else:
                newRes['result'] = item.string
        newRes['sport'] = name_to_link(row.find("div",class_="td col3").string)
        newRes['event'] = name_to_link(row.find("div",class_="td col4").string)
        newRes['olympics'] = row.find_previous("a")['href'].split("/")[-1].strip()
        results.append(newRes)
    return results
