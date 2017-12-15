import requests
from bs4 import BeautifulSoup
import warnings
from flask_table import Table, Col
import os
import json

warnings.filterwarnings("ignore")

main_list = []
checked_list = []
graph = {}
max_number = 150

class ItemTable(Table):
    name = Col('Name')
    github_username = Col('Github Username')
    link = Col('Link')

class Item(object):
    def __init__(self, name, github_username, link):
        self.name = name
        self.github_username = github_username
        self.link = link

class user:
    def __init__(self,name,followers_list,following_list):
        self.name = name
        self.followers_list = followers_list
        self.following_list = following_list
        self.folllowing_node_list = []
        self.folllowers_node_list = []

def get_data(username, no):
    if no == 0:
        z = 'followers'
    else:
        z = 'following'
    # these lines of code gets the list of followers or the following on the first page
    # when there are no further pages of followers or following. And if there are go forward with the next page
    s = requests.Session()
    final=[]
    x = 1
    pages = [""]
    data = []
    while(pages != [] and x <= max_number/50):
        r = s.get('https://github.com/' + username + '?page=' +  str(x) + '&tab=' + z) #first getting all the followers for z=0, and following for z=1
        soup = BeautifulSoup(r.text)
        data = data + soup.find_all("div", {"class" : "d-table col-12 width-full py-4 border-bottom border-gray-light"})
        pages = soup.find_all("div", {"class" : "pagination"})
        x += 1
   # getting company and area.
    for i in data:
        username = i.find_all("a")[0]['href']
        try:
            company = i.find_all("span", {"class" : "mr-3"})[0].text.strip()
        except:
            company = "xxxxx"
        try:
            area = i.find_all("p", {"class" : "text-gray text-small mb-0"})[0].text.strip()
        except:
            area = "xxxxx"
        soup2 = BeautifulSoup(str(i))
        name = soup2.find_all("span",{"class" : "f4 link-gray-dark"})[0].text
        final.append([username,company,area,name])
    return final

def string_matching(username, mode, organisations,name, main_list,graph_list):
    for org in organisations:
        try:
            if(mode in organisations):
                if [username,name] not in main_list:
                    main_list.append([username,name])
                if username not in graph_list:
                    graph_list.append(username)
        except:
            pass

def scrape_org(org,main_list,organisation):
     s = requests.Session()
     r = s.get('https://github.com/orgs/'+org+'/people')
     soup = BeautifulSoup(r.text)
     data = soup.find_all("li", {"class" : "table-list-item member-list-item js-bulk-actions-item "})

     for i in data:
         soup2=BeautifulSoup(str(i))
         data2=soup2.find_all("div",{"class" : "table-list-cell py-3 pl-3 v-align-middle member-avatar-cell css-truncate pr-0"})
         username = data2[0].find_all("a")[0]['href']
         data3 = soup2.find_all("div",{"class" : "table-list-cell py-3 v-align-middle member-info css-truncate pl-3"})
         name = data3[0].find_all("a")[0].text.strip()
         main_list.append([username,name])

def update_org_list(main_list,organisation):
    s = requests.Session()
    for i in main_list:
         r = s.get('https://github.com/'+i[0])
         soup = BeautifulSoup(r.text)
         data = soup.find_all("li",{"aria-label":"Organization"})
         try:
             if data[0].text not in organisation:
                 organisation.append(data[0].text)
         except:
             continue
    return organisation

def scrape_org_2(org,main_list,organisation):
    org.replace(" ","+")
    s = requests.Session()
    count = 1
    k = "https://github.com/search?p="+str(count)+"&q="+org+"+type%3Auser&type=Users&utf8=%E2%9C%93"
    r = s.get(k)

    soup = BeautifulSoup(r.text,"lxml")
    data = soup.find_all("div",{"class":"user-list-info ml-2"})
    while data!=[]:
        for i in data:
            username = i.find_all("a")[0]['href']
            name = i.find_all("span",{"class":"f4 ml-1"})[0].text.strip()
            main_list.append([username,name])
        count+=1
        k = "https://github.com/search?p="+str(count)+"&q="+org+"+type%3Auser&type=Users&utf8=%E2%9C%93"
        r = s.get(k)
        soup = BeautifulSoup(r.text,"lxml")
        data = soup.find_all("div",{"class":"user-list-info ml-2"})

# scraping the github pages
def scrape(username, main_list, checked_list, organisation):
    primary = user(username, [], [])
    secondary = []
    checked_list.append("/" + username)
    data1 = get_data(username,0)   #calling get_data function with the given username as input and 0 = followers.
    data2 = get_data(username,1) #calling get_data function with the given username as input and 1 = followers.
    # data contains all the links to the profile url fo the followers and following
    followers_graph = []
    following_graph = []
    k = username
    for i in data1:
        username = i[0]
        company = (''.join(e for e in i[1] if e.isalpha())).lower()  # removing all noise in the company name
        area = (''.join(e for e in i[2] if e.isalpha())).lower()   # removing all noise in the area name
        string_matching(username,area,organisation,i[3],main_list,followers_graph)  # checking area matches with the organisation or not
        string_matching(username,company,organisation,i[3],main_list,followers_graph) # checking area matches with the organisation or not
    for i in data2:
        username = i[0]
        company = (''.join(e for e in i[1] if e.isalpha())).lower()  # removing all noise in the company name
        area = (''.join(e for e in i[2] if e.isalpha())).lower()   # removing all noise in the area name
        string_matching(username,area,organisation,i[3],main_list,following_graph)  # checking area matches with the organisation or not
        string_matching(username,company,organisation,i[3],main_list,following_graph) # checking area matches with the organisation or not
    # getting details about the first followers list.
    graph[k]=[following_graph,followers_graph]
    for j in primary.followers_list:
        checked_list.append(j)
        data = get_data(j,0) # getting data of the followers of the followers
        temp_user = user(j, [], [])

        for i in data:
            username = i[0]
            company = (''.join(e for e in i[1] if e.isalpha())).lower()
            area = (''.join(e for e in i[2] if e.isalpha())).lower()
            string_matching(username,area,organisation,i[3],main_list)
            string_matching(username,company,organisation,i[3],main_list)
        data = get_data(j,1) # getting data of the following of the followers

        for i in data:
            username = i[0]
            company = (''.join(e for e in i[1] if e.isalpha())).lower()
            area = (''.join(e for e in i[2] if e.isalpha())).lower()
            string_matching(username,area,organisation,i[3],main_list)
            string_matching(username,company,organisation,i[3],main_list)
        primary.folllowers_node_list.append(temp_user)
        secondary.append(temp_user)

    for j in primary.following_list:
        if j not in checked_list:
            checked_list.append(j)
        data = get_data(j,1) # getting data of the following of the following
        temp_user = user(j, [], [])
        for i in data:
            username = i[0]
            company = (''.join(e for e in i[1] if e.isalpha())).lower()
            area = (''.join(e for e in i[2] if e.isalpha())).lower()
            string_matching(username,area,organisation,i[3],main_list)
            string_matching(username,company,organisation,i[3],main_list)
        primary.folllowing_node_list.append(temp_user)
        secondary.append(temp_user)
        data=get_data(j,0) # getting data of the followers of the following
        for i in data:
            username = i[0]
            company = (''.join(e for e in i[1] if e.isalpha())).lower()
            area = (''.join(e for e in i[2] if e.isalpha())).lower()
            string_matching(name,area,organisation,i[3],main_list)
            string_matching(name,company,organisation,i[3],main_list)

def get_json(org):
    d = {"nodes":[],"links":[]}
    for i in graph:
        dt = {}
        dt["id"]=i
        dt["group"]=1
        d["nodes"].append(dt)
    for i in graph:
        for j in graph[i]:
            for k in j:
                dt={}
                dt["source"]=i
                dt["target"]=k[1::]
                dt["value"]=10
                d["links"].append(dt)
    string_json = json.dumps(d)
    filename = org + ".json"
    f = open(os.path.join(os.getcwd(), "static", filename), "w")
    f.write(string_json)
    f.close()

def find(main_list, checked_list, organisation, org):
    for i in main_list:
        if i[0] not in checked_list:
            scrape(i[0][1::], main_list, checked_list, organisation)  # recursion on every user who is not there in the main list.
    js = get_json(org)

def make_html(fullpath, table):
    f = open(fullpath, "w")
    header_r = open("query_header.html", "r")
    header = header_r.read()
    f.write(header)
    header_r.close()
    f.write(table.__html__())
    footer_r = open("query_footer.html", "r")
    footer = footer_r.read()
    f.write(footer)
    footer_r.close()
    f.close()

def creating_objs(main_list, org):
    items = []
    for i in main_list:
        items.append(Item(i[1].encode('ascii', 'ignore'),i[0].encode('ascii', 'ignore'),"https://github.com"+i[0].encode('ascii', 'ignore')))
    table = ItemTable(items)
    filename = org + ".html"
    fullpath = os.path.join(os.getcwd(), "templates", filename)
    make_html(fullpath, table)
    return items

def main(org):
    main_list = []
    organisation = []
    checked_list = []
    scrape_org(org,main_list,organisation)
    # scrape_org_2(org,main_list,organisation)
    update_org_list(main_list,organisation)
    for i in range(len(organisation)):
        organisation[i] = (''.join(e for e in organisation[i] if e.isalpha())).lower()
    find(main_list, checked_list, organisation, org)
    items = creating_objs(main_list, org)
    return items

# program starts from here
if __name__ == '__main__':
    org = raw_input("organisation name : ") #getting organisation as input
    main(org)
