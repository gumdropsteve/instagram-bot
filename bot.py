# timing 
import time
import random
from time import sleep
# reading
import numpy as np
import pandas as pd
# recording
import csv
from datetime import datetime
# webdriver
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException 

# .js help
from infos import scroll
# functions
from helpers import check_xpath
# urls
from infos import ig_log_page, ig_tags_url
# data (loaded here for future multitasking)
from infos import follows_users, by_users, unfollow_log 
from infos import verified_unfollow_log, redo_unfollow_log, re_verified_unfollow_log
# paths
from infos import username_box, password_box, save_info_popup
from infos import following_button, unfollow_button, follow_button 
from infos import comment_button, comment_box, like
# misc
from infos import ig_tags_url


class InstagramBot:

    def __init__(self, username):
        # tag the options field
        options = webdriver.FirefoxOptions()  
        # disable push/popups 
        options.set_preference("dom.push.enabled", False)  
        # set user
        self.username = username
        # set driver with options 
        self.driver = webdriver.Firefox(options=options)
        # minimize browser window
        self.driver.minimize_window()

    def login(self, password):
        """loads and logs in to instagram
        """
        # load instagram login page
        self.driver.get(ig_log_page)
        # wait (hedge load time)
        sleep(3)
        # find user box, type in account id
        self.driver.find_element_by_xpath(username_box).send_keys(self.username)
        # find key box and call locksmith, he should be able to punch in
        self.driver.find_element_by_xpath(password_box).send_keys(password, Keys.RETURN)
        # hedge request/load time 
        sleep(3)
        # take care if "save info" pop-up page pops up
        check_xpath(webdriver=self.driver, xpath=save_info_popup, click=True)

    def gather_posts(self, hashtag, scroll_range=5, 
                     limit=False, certify=True, r_log_on=True):
        """collects group of post urls by hashtag

        input) 
        > hashtag 
            >> hashtag from which to gather posts

        output)
        > post_hrefs
            >> collection of urls to posts form hashtag 
        """
        # determine day of week and key strings
        day = time.strftime("%A").lower()
        key = time.strftime("%Y%m%d_%H%M%S")
        # load the webpage to which the image belongs 
        self.driver.get(ig_tags_url + hashtag + '/')
        # hedge load time
        sleep(3)
        # set base collection for hrefs 
        post_hrefs = []
        # load n (scroll_range) scrolls of pictures
        for n in range(scroll_range):
            # this should work
            try:
                # it's almost like we're human
                self.driver.execute_script(scroll)
                # so pause and maybe they won't catch on
                sleep(2)
                # get page tags
                hrefs_in_view = self.driver.find_elements_by_tag_name('a')
                # finding relevant hrefs
                hrefs_in_view = [elem.get_attribute('href') for elem in hrefs_in_view
                                 if '.com/p/' in elem.get_attribute('href')]
                # building list of unique photos
                [post_hrefs.append(href) for href in hrefs_in_view if href not in post_hrefs]
                # so as not to spam
                if n % 2 != 0:
                    # display length of list to user
                    print("Check: pic href length " + str(len(post_hrefs)))
            # but just in case
            except:
                # let us know it didn't work, and which iteration 
                print(f"except Exception: #{n} gathering photos")
                # and keep moving
                continue
        # check for limit
        if limit != False:
            # check if we are over the limit
            if len(post_hrefs) > limit:
                # apply the limit 
                post_hrefs = post_hrefs[:limit]
        # identify log route
        route = 'data/made/post_hrefs/log'
        # dataframe this hashtag's existing csv file 
        log = pd.read_csv(route)     
        # are we making sure these are unique? (default : yes)
        if certify:
            # tag previously seen hrefs
            repeats = [href for href in post_hrefs if href in list(log.href)]
            # remove previously seen hrefs 
            post_hrefs = [href for href in post_hrefs if href not in repeats]
            # are we recording repeats? (default : yes)
            if r_log_on:
                # tag repeat log route
                r_route = 'data/made/post_hrefs/r_log'
                # read in repeat log
                repeat_log = pd.read_csv(r_route)
                # build dataframe
                r_df = pd.DataFrame(repeats, columns=['href'])
                # make lists for day of week, key, and tag columns
                r_df['dow'] = (  (  (day + ',') * (len(r_df)-1) ) + day).split(',')
                r_df['key'] = (  (  (key + ',') * (len(r_df)-1) ) + key).split(',')
                r_df['tag'] = (((hashtag + ',') * (len(r_df)-1) ) + hashtag).split(',')    
                # join and write the new repeat log
                pd.concat([repeat_log, r_df], axis=0).to_csv(r_route, index=False)       
        # define dataframe of hrefs
        df = pd.DataFrame(post_hrefs, columns=['href'])
        # make lists for day of week and key columns
        df['dow'] = (  (  (day + ',') * (len(df)-1) ) + day).split(',')
        df['key'] = (  (  (key + ',') * (len(df)-1) ) + key).split(',')
        df['tag'] = (((hashtag + ',') * (len(df)-1) ) + hashtag).split(',')
        # add new dataframe to existing 
        df = pd.concat([log, df], axis=0)
        # write the new dataframe over the old dataframe in csv (w/o index)
        df.to_csv(route, index=False)
        # output collection of hrefs
        return post_hrefs        

    def like_posts(self, hashtag, hrefs, indicator_thresh=5):
        """load and 'like' posts from given list

        input)
        > hashtag
            >> hashtag from which the posts have been collected
        > hrefs
            >> list of posts (by url) to be liked
        > indicator_thresh
            >> how many posts to process between printing progress 
        """
        # note how many posts there are 
        n_unique_posts = len(hrefs)
        # go through each one
        for post_href in hrefs:
            # load the post
            self.driver.get(post_href)
            # hedge for whatever
            sleep(5)
            # move around a bit, make sure we can see the heart (like button)
            self.driver.execute_script(scroll)
            # this should work
            try:
                # find the like button 
                like_button = lambda: self.driver.find_element_by_xpath(like).click()
                # click the like button
                like_button().click()
                # hedge over-liking
                sleep(10)
            # if it doesn't work
            except:
                # don't really have a backup plan.. so take a break ig..
                sleep(2)
            # update count of remaining posts
            n_unique_posts -= 1
            # check for asked indication
            if n_unique_posts % indicator_thresh == 0:
                # let us know how many remain
                print(f'#{hashtag} : remaining = {n_unique_posts}')

    def comment(self, post, comment):
        '''load given post then comment given comment
        '''
        # pull up post 
        self.driver.get(post)
        # locate & click comment button
        self.driver.find_element_by_xpath(comment_button).click()
        # write out hashtags
        self.driver.find_element_by_xpath(comment_box).send_keys(comment, Keys.RETURN)
        # let us know what happened
        print(f'\ncomment added to post\npost: {post}\ncomment: {comment}\n')

    def close_browser(self):
        """closes webdriver
        """
        self.driver.close()  
        
    def generate_actionable_uls(self, potential_accounts, n, white_list_accounts):
        """identify accounts elgible for action from pd dataframe via 
        compairson to dataframe of non/previously-actionable accounts

        inputs:
        > potential_accounts
            >> pandas dataframe of accounts up for action
                > with account urls in .user_profile column
        > n
            >> number of accounts on which action will be taken in this round
        > white_list_accounts
            >> pandas dataframe of accounts which have already been acted upon
                > with account urls in .user_profile column

        output:
        > list of urls belonging to potential_accounts not found in white_list_accounts
        """
        # pull/tag potential urls 
        potential_urls = [url for url in potential_accounts.user_profile]
        # pull/tag previously seen urls
        already_actioned = [url for url in white_list_accounts.user_profile]
        # forget already actioned urls
        elgible_urls = [url for url in potential_urls if url not in already_actioned]
        # range matters
        if n != False:
            # shrink numer of accounts to desired range
            elgible_urls = elgible_urls[:n]
        # output actionable accounts
        return elgible_urls

    def unfollow(self, account_url):
        """unfollow given account 

        inputs:
        > account_url
            >> url of account to unfollow

        output:
        > list detailing transaction
            >> check/click 'following', check/click 'unfollowing', datetime
        """
        # load the account's profile
        self.driver.get(account_url) 
        # test for/find and click the 'following' button (0=success)
        ntract_following = check_xpath(webdriver=self.driver, xpath=following_button, click=True, hedge_load=5)
        # following button went well
        if ntract_following == 0:
            # wait a bit (hedge load)
            sleep(3)                    
            # test for/find and click the 'unfollow' button (0=success)
            ntract_unfollow = check_xpath(webdriver=self.driver, xpath=unfollow_button, click=True)
        # following buttion did not go well
        else:
            # unfollow no longer possible
            ntract_unfollow = 'nan'
        # output instance of unfollowing for log
        return [ntract_following, ntract_unfollow, datetime.now()]

    def record(self, record, log):
        """record given info into given csv 

        inputs:
        > record
            >> information to be recorded
        > log
            >> csv file where information is to be recorded
        """
        # open up that redo log 
        with open(log, 'a') as f:
            # fit the writer
            writer = csv.writer(f)
            # document the information
            writer.writerow(record)
