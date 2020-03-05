import pickle
import time
from pathlib import Path

from bs4 import BeautifulSoup
from selenium import webdriver


# from webdriver_manager.chrome import ChromeDriverManager
# import requests


def create_new_browser(driver_path):
    # browser = webdriver.Chrome(ChromeDriverManager().install())
    browser = webdriver.Chrome(driver_path)
    with open(session_file, 'wb') as f:
        params = {'session_id': browser.session_id, "server_url": browser.command_executor._url}
        pickle.dump(params, f)
    return browser


def call_browser(logged_in, session_file, driver_path):
    if not Path(session_file).exists():
        browser = create_new_browser(driver_path=driver_path)
        logged_in = False
    else:
        logged_in = True
        with open(session_file, 'rb') as f:
            params = pickle.load(f)
            try:
                browser = webdriver.Remote(command_executor=params['server_url'])
                browser.quit()  # Quit the new browser opened by 'start_session'
                browser.session_id = params['session_id']
                # browser.execute_script('window.open("");')  # Open a blank page
                browser.switch_to.window(browser.window_handles[-1])
            except:
                browser = create_new_browser(driver_path=driver_path)
    return browser


def examine_logged_in(browser):
    if not logged_in:
        browser.get('https://www.linkedin.com/login')
        # Log in credentials
        file = open('credentials.txt')
        lines = file.readlines()
        username = lines[0]
        password = lines[1]

        # Entre the username and password
        elementID = browser.find_element_by_id('username')
        elementID.send_keys(username)

        elementID = browser.find_element_by_id('password')
        elementID.send_keys(password)
        elementID.submit()


def adjust_page(browser):
    # Entre into the personal profile page
    browser.get(link)

    # Get scroll height
    last_height = browser.execute_script("return document.body.scrollHeight")

    # Set the waiting time for loading page contents
    SCROLL_PAUSE_TIME = 5

    # Scroll the page to load info
    for _ in range(3):
        # Scroll down to bottom
        browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")

        # Wait to load page
        time.sleep(SCROLL_PAUSE_TIME)

        # Calculate new scroll height and compare with last scroll height
        new_height = browser.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height


if __name__ == '__main__':
    # Initialising the browser
    driver_path = '/Users/bojanfu/.wdm/drivers/chromedriver/80.0.3987.106/mac64/chromedriver'
    session_file = 'browser_session.data'
    global logged_in
    logged_in = False  # TODO: examine if the browser has logged in to LinkedIn

    browser = call_browser(logged_in, session_file, driver_path)
    examine_logged_in(browser)

    link = "https://www.linkedin.com/in/erikaregner/"
    adjust_page(browser)

    # ---------------------------------------------
    """Finding process:
    Name section: 'flex-1 mr5'
    -> ul
    -> h2
    -> ul
    Experiences section: ul, class="pv-profile-section__section-info section-info pv-profile-section__section-info--has-more"
    -> some <li>s, one experience with one <li> tag 
    """
    # Start to make soup
    src = browser.page_source
    soup = BeautifulSoup(src, 'lxml')

    # Find the name section
    name_div = soup.find('div', {'class': 'flex-1 mr5'})
    name_loc = name_div.find_all('ul')
    name = name_loc[0].find('li').get_text().strip()
    print("Processing:", name)

    # Location tag
    loc = name_loc[1].find('li').get_text().strip()

    profile_title = name_div.find('h2').get_text().strip()

    # Connection amount
    connection = name_loc[1].find_all('li')
    connection = connection[1].get_text().strip()

    # Initialising
    count = 0
    job_title = []
    company_name = []
    joining_date = []
    time_period = []
    location = []
    description = []
    experience_number = 0
    experience_exist = True

    # -------------------------------------
    try:
        # NEW EXPERIENCE CRAWLER
        exp_section = soup.find('section', {'class': "pv-profile-section experience-section ember-view"})
        ul_tags = exp_section.find('ul')
        li_tag_1 = ul_tags.find('li')
        li_siblings = li_tag_1.next_siblings
        experience_number = len(list(li_siblings))
        print(experience_number, ' experiences listed.')

        for n in range(experience_number):
            li_tags = ul_tags.find_all('li', {"class": "pv-entity__position-group-pager pv-profile-section__list-item "
                                                       "ember-view"})[n]
            div_tags = li_tags.find('div', {'class': "display-flex justify-space-between full-width"})
            a_tags = div_tags.find('a', {"class": "full-width ember-view"})

            # JOB TITLE
            job_title_get = False
            try:
                _ = a_tags.find('div', {
                    "class": "pv-entity__summary-info pv-entity__summary-info--background-section mb2"}).find('h3', {
                    "class": "t-16 t-black t-bold"}).get_text().strip()
                if _ == '' or _ is None:
                    _ == "No job title. ('' or None founded)"
                    error = '(1) _ is: ', _, type(_)
                to_append = _
                job_title_get = True  # TODO: Logic here is not clear enough
            except (AttributeError, IndexError) as e:
                error = e
                to_append = "No job title."
            # alter
            try:
                _ = a_tags.find('div',
                                {"class": "pv-entity__summary-info pv-entity__summary-info--background-section"}).find(
                    'h3').get_text().strip()
                if _ == '' or _ is None:
                    _ == "No job title."
                    error = '(2) _ is: ', _, type(_)
                to_append = _
            except (AttributeError, IndexError) as e:
                error = e
                if job_title_get is not True:
                    to_append = "No job title."
            job_title.append(to_append)
            if to_append == "No job title.":
                print("Error occurred (job title): ", error)

            # COMPANY NAME
            company_name_get = False
            try:
                _ = a_tags.find('p', {"class": "pv-entity__secondary-title t-14 t-black t-normal"}).get_text().strip()
                if _ == '' or _ is None:
                    _ = "No Company Name."
                to_append = _
                company_name_get = True
            except (AttributeError, IndexError) as e:
                error = e
                to_append = "No Company Name."
            # alter
            try:
                _ = a_tags.find('h3', {"class": "t-16 t-black t-bold"}).find_all('span')[1].get_text().strip()
                if _ == '' or _ is None:
                    _ = "No Company Name."
                to_append = _
            except (AttributeError, IndexError) as e:
                error = e
                if company_name_get is not True:
                    to_append = "No Company Name."
            company_name.append(_)
            if to_append == "No Company Name.":
                print("Error occurred (company name): ", error)

            # JOINING DATE
            try:
                _ = a_tags.find('h4', {"class": "pv-entity__date-range t-14 t-black--light t-normal"}).find_all('span')[
                    1].get_text().strip()
                if _ == '' or _ is None:
                    _ = "No joining date."
                joining_date.append(_)
            except (AttributeError, IndexError) as e:
                print("Error occurred (date):", e)
                joining_date.append("No joining date.")

            # TIME PERIOD
            time_get = False
            try:
                _ = a_tags.find_all('h4')[1].find_all('span')[1].get_text().strip()
                if _ == '' or _ is None:
                    _ == "No time period."
                to_append = _
                time_get = True
            except (AttributeError, IndexError) as e:
                error = e
                to_append = "No time period."
            # alter
            try:
                _ = a_tags.find_all('h4')[0].find_all('span')[1].get_text().strip()
                if _ == '' or _ is None:
                    _ == "No time period."
                to_append = _
            except (AttributeError, IndexError) as e:
                error = e
                if time_get is not True:
                    to_append = "No time period."
            time_period.append(_)
            if to_append == "No time period.":
                print("Error occurred (time period): ", error)

            # LOCATION
            try:
                _ = a_tags.find_all('h4')[2].find_all('span')[1].get_text().strip()
                if _ == '' or _ is None:
                    _ = "No location."
                location.append(_)
            except (AttributeError, IndexError) as e:
                print('Error occurred (location):', e)
                location.append("No location.")

            # DESCRIPTION
            try:
                _ = \
                    div_tags.find('div', {'class': "pv-entity__extra-details t-14 t-black--light ember-view"}).find_all(
                        'p')[
                        0].get_text().strip()
                if _ == '' or _ is None:
                    _ = "No description."
                description.append(_)
            except (AttributeError, IndexError) as e:
                print('Error occurred (description):', e)
                description.append("No description.")
            # Additional processing
            if description[-1].endswith('see more'):
                # delete 'see more'
                description[-1] = description[-1][:-8]
                description[-1] = description[-1].strip()
                if description[-1].endswith('…'):
                    # delete the sign with 3 dots
                    description[-1] = description[-1][:-1]
                    description[-1] = description[-1].strip()
            count += 1
    except (AttributeError, IndexError) as e:
        print(e)
        experience_exist = False
        print("No experiences found.")

    '''# Experience section
    '''

    # Initialising
    college_name = []
    degree_name = []
    degree_description = []
    degree_year = []
    education_number = 0
    edu_exist = True
    education_found = []

    try:
        # NEW EDUCATION CRAWLER
        edu_section = soup.find('section', {'id': 'education-section'}).find('ul')
        edu_secs = edu_section.find_all('li', {
            'class': "pv-profile-section__list-item pv-education-entity pv-profile-section__card-item ember-view"})
        education_number = len(list(edu_secs))
        print(education_number, ' educations listed.')

        count = 0

        for n in range(education_number):
            edu_secs = edu_section.find_all('li', {
                'class': "pv-profile-section__list-item pv-education-entity pv-profile-section__card-item ember-view"})[
                n]

            try:
                _ = edu_secs.find_all('div')[4].find('h3',
                                                     {
                                                         'class': "pv-entity__school-name t-16 t-black t-bold"}).get_text().strip()
                if _ == '' or _ is None:
                    _ = "No uni name."
                college_name.append(_)
            except:
                college_name.append("No uni name.")

            try:
                _ = edu_secs.find('p',
                                  {
                                      'class': 'pv-entity__secondary-title pv-entity__degree-name t-14 t-black t-normal'}).find(
                    'span', {'class': "pv-entity__comma-item"}).get_text().strip()
                if _ == '' or _ is None:
                    _ = "No degree name."
                degree_name.append(_)
            except:
                degree_name.append("No degree name.")

            try:
                _ = \
                    edu_secs.find('p',
                                  {
                                      'class': 'pv-entity__secondary-title pv-entity__fos t-14 t-black t-normal'}).find_all(
                        'span')[1].get_text().strip()
                if _ == '' or _ is None:
                    _ = "No degree description."
                degree_description.append(_)
            except:
                degree_description.append("No degree description.")

            try:
                _ = edu_secs.find('p', {'class': 'pv-entity__dates t-14 t-black--light t-normal'}).find_all('span')[
                    1].get_text().strip()
                if _ == '' or _ is None:
                    _ = "No degree year."
                degree_year.append(_)
            except:
                degree_year.append("No degree year.")
            count += 1
    except:
        edu_exist = False
        print("No education found.")

    # ---------------------------------------------
    # General info
    info_person = [link, name, profile_title, loc, connection]

    # See if there exist some experiences
    if experience_exist is False:
        no_experience = "No experiences found!"
    else:
        experience = [company_name, job_title, joining_date, time_period, location, description]

    # See if there exist some education
    if edu_exist is False:
        no_education = "No education found!"
    else:
        education_found = [college_name, degree_name, degree_description, degree_year]

    # Set the file name with name of the person
    filename = 'LinkedIn_Profile_' + name.replace(' ', '_') + '.txt'
    print("Information are being writing into the text file: " + filename + " ...")
    # Write info into a file
    with open(filename, 'w') as text_file:
        text_file.write('[' + name + ']' + '(' + link + ')' + '\n')
        for item in info_person[2:5]:
            text_file.write('* ' + item + '\n')

        # Writing experience
        text_file.write('\n' + '### ' + 'EXPERIENCE:' + '\n')
        if experience_exist is True:
            for num in range(experience_number):
                for item in experience:
                    try:
                        text_file.write(item[num] + '\n')
                    except:
                        text_file.write('None here' + '\n')
                text_file.write('\n')
        else:
            text_file.write(no_experience + '\n')

        # Writing education
        text_file.write('\n' + '### ' + 'EDUCATION:' + '\n')
        if edu_exist is True:
            for num in range(education_number):
                for item in education_found:
                    try:
                        text_file.write(item[num] + '\n')
                    except:
                        text_file.write('None here' + '\n')
                text_file.write('\n')
        else:
            text_file.write(no_education + '\n')
        text_file.write('\n' + '------------- END -------------')

    print('Writing completed!')
