import configparser, re, json, pymysql, furl, sys
from selenium import webdriver
from urllib.parse import urlsplit, parse_qs
from pprint import pprint



class PageParser:
    def __init__(self, url):
        """Init

        Args:
            url (string): url link
        """
        
        driver.get('https://' + url if 'https' not in url else url)
        self.data = {
            'url' : url,
            'id'  : re.findall(r'resume\/([^\?]+)', url)[0]
        }
        
        self.__parse()
        self.__load_to_db()


    def __parse(self):
        """Parse data from url """

        #Parse age and gender find
        self.data['gender'] = driver.find_element_by_xpath("//span[@data-qa=\"resume-personal-gender\"]").text
        self.data['age'] = re.findall(r'\d+',
            driver.find_element_by_xpath("//span[@data-qa=\"resume-personal-age\"]").text)[0]

        #Parse salary, profession, time practice
        self.data['prof'] = driver.find_element_by_xpath('//span[@data-qa="resume-block-title-position"]').text

        try:
            self.data['salary'] = driver.find_element_by_xpath('//span[@data-qa="resume-block-salary"]').text
            self.data['salary'] = re.sub(r'[^\d\w \.]', '', self.data['salary'])
        except:
            self.data['salary'] = 'Empty'
        
        self.data['practice'] = driver.find_element_by_xpath('//span[@class="resume-block__title-text resume-block__title-text_sub"]').text

        #Practice time formatting (year*12+months)
        self.data['practice'] = re.findall(r'(\d+.*)', self.data['practice'])[0]
        self.data['practice'] = re.sub(r'( лет| год| года)', '*12+', self.data['practice'])
        self.data['practice'] = re.sub(r'( месяц\w+)', '*1', self.data['practice'])
        self.data['practice'] = re.sub(r' ', '', self.data['practice'])

        try:
            self.data['practice'] = str(eval(self.data['practice']))
        except:
            self.data['practice'] = re.sub(r'\w', '', self.data['practice']) + '0'
            self.data['practice'] = str(eval(self.data['practice']))
        
        #Parse town and old works
        self.data['town'] = driver.find_element_by_xpath('//span[@data-qa="resume-personal-address"]').text
        self.data['old_works'] = json.dumps([
                block.text.split('\n')[2]
                for block in  driver.find_elements_by_xpath(
                    '//div[@class="resume-block-item-gap"]/div[@class="bloko-columns-row"]/div[@class="resume-block-item-gap"]')
            ], ensure_ascii=False)

        
        #Study organizations and spec
        try:
            education_block = self.__driver__.find_elements_by_xpath('//div[@data-qa="resume-block-education"]')
        except:
            education_block = "Empty"


        self.data['study'] = json.dumps(
                {
                    item.find_element_by_xpath('//div[@data-qa="resume-block-education-name"]').text :
                        item.find_element_by_xpath('//div[@data-qa="resume-block-education-organization"]/span').text
                    for item in education_block[0].find_elements_by_xpath('//div[@data-qa="resume-block-education-item"]')
                },
                ensure_ascii=False
            ) if education_block != "Empty" else 'Empty'

        #Parse about block
        try :
            self.data['about'] = self.__driver__.find_element_by_xpath('//div[@data-qa="resume-block-skills-content"]/span').text
        except :
            self.data['about'] = 'Empty'
    
    def __load_to_db(self):
        """Load data to db"""

        cursor = con.cursor()
        cursor.execute("""CREATE TABLE IF NOT EXISTS resumes (
            id TEXT,
            url TEXT, 
            gender TEXT,
            age TEXT, 
            prof TEXT, 
            salary TEXT, 
            practice TEXT, 
            town TEXT, 
            old_works TEXT,  
            study TEXT, 
            about TEXT);""")

        #Find parsed user
        cursor.execute("SELECT * FROM resumes WHERE id = %s", [self.data['id']])
        req = cursor.fetchall()

        #If user in bd, update info
        if len(req) != 0:
            cursor.execute("""
            UPDATE resumes
            SET """ + ', '.join([k + '=' + json.dumps(self.data[k]) for k in self.data]) +
            """ WHERE id = %s""", [self.data['id']])

            #Debug monitoring (fitcha)
            print('Mb yeah! +-1!!!')

        #If user not found in db, insert new user in db
        else:
            cursor.execute(
                "INSERT INTO resumes (" + ', '.join(list(self.data.keys())) + 
                ") VALUES(" + ('%s, ' * len(self.data.values()))[:-2] + ')',
                list(self.data.values()))

            #Debug monitoring (fitcha)
            print('Yeah. +1!!!')

        #Commit updates
        con.commit()
        cursor.close()
    
    @staticmethod
    def find_links_from_url(url):
        """Find links on all pages from hh.ru 
        (early configurate town and another params)

        Args:
            url (str): url page, early configurate

        Returns:
            list strings : found links in list format
        """

        #Split url, (page number appending or change)
        url_splited = urlsplit(url)
        params = {
            k : v 
            for k, v in parse_qs(url_splited.query).items()
        }
        params['page'] = 1

        url = furl.furl(url_splited.scheme + '://' + url_splited.netloc + url_splited.path)
        url.args = params

        driver_finder = webdriver.Chrome(executable_path=config['PATH']['chromedriver'])
        result = []

        while (True):
            driver_finder.get(url.url)
            
            resume_items_arr = driver_finder.find_elements_by_xpath('//div[@data-qa="resume-serp__resume-header"]/span/a')
            result += [item.get_attribute('href') for item in resume_items_arr]

            #Check "Next" button on page
            try:
                tmp = driver_finder.find_element_by_xpath('//a[@data-qa="pager-next"]')
                url.args['page'] += 1
            except:
                break
        
        driver_finder.close()
        return result


if __name__ == '__main__':

    #Read attrs
    attrs = {}
    for param in sys.argv:
        if param[0] == '-':
            try:
                attrs[param] = sys.argv[sys.argv.index(param) + 1]
            except:
                attrs[param] = None

    #Parse current page
    if '-c' in attrs.keys() or '--current' in attrs.keys():
        #Load config file
        config = configparser.ConfigParser()
        config.read('settings.ini')

        #Create driver and connection
        driver = webdriver.Chrome(executable_path=config['PATH']['chromedriver'])
        con = pymysql.connect(
            host=config['DB']['host'], 
            user=config['DB']['login'], 
            password=config['DB']['password'], 
            db=config['DB']['db'])
        
        #Parse link
        test = PageParser(attrs['-c'] if '-c' in attrs.keys() else attrs['--current'])

        #Close driver
        driver.close()

    #Helper
    elif ('-h' in attrs.keys() or '--help' in attrs.keys()) or len(attrs) == 0:
        print('''
        Parser help page
        -c or --current [url page] - parse current resume
        -a or --all     [url page] - parse pages from page with resumes
        -h or --help               - help
        '''
        )
    
    #Parse all pages
    elif '-a' in attrs.keys() or '--all' in attrs.keys():
        #Load config file
        config = configparser.ConfigParser()
        config.read('settings.ini')

        #Create driver and connection
        driver = webdriver.Chrome(executable_path=config['PATH']['chromedriver'])
        con = pymysql.connect(
            host=config['DB']['host'], 
            user=config['DB']['login'], 
            password=config['DB']['password'], 
            db=config['DB']['db'])
        
        for link in PageParser.find_links_from_url(attrs['-a'] if '-a' in attrs.keys() else attrs['--all']):
            test = PageParser(link)
    
        #Close driver
        driver.close()