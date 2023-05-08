import requests
import json
import time
import os
import atexit

repos_filename = 'files/repos.json'
credentials_filename = 'credentials.json'
api_limiter = (60 ** 2) / 5000.0  # max possible requests per hour allowed by Authenticated API
last_crawled = 188000000
crawl_goal = last_crawled + 20000
repos_crawled = 0
t = time.time()
page_size = 100


class CrawlerException(Exception):
    pass


def wait():
    global t
    sleep = max(0, api_limiter - (time.time() - t))  # 0 delay as lower bound
    time.sleep(sleep)
    t = time.time()


def close_file():
    global last_crawled
    print(f'Stopping crawler after repo {last_crawled}.')
    with open(repos_filename, 'a+') as file:
        file.write('\n]')


def make_request(url):
    headers = {'Authorization': f"Bearer {basicAuthCredentials}"}
    r = requests.get(url, headers = headers)
    if r.status_code > 400:
        raise CrawlerException('Query failed with message: ' + r.text)
    return json.loads(r.text)


def retrieve_repo(page):
    repo_list = make_request(f'https://api.github.com/search/repositories?q=org:microsoft&per_page={page_size}&page={page}')
    return repo_list


def retrieve_languages(name):
    language_list = make_request(f'https://api.github.com/repos/{name}/languages')
    return language_list


def retrieve_commits(name):
    commits_list = make_request(f'https://api.github.com/repos/{name}/commits')
    return list(map(lambda commit: commit['commit']['message'], commits_list))


def crawl_repos():
    global last_crawled
    global repos_crawled

    with open(repos_filename, 'w') as file:
        file.write('[\n')

    t = time.time()
    page = 1
    number_of_repositories = page_size
    while repos_crawled < number_of_repositories:
        try:
            print(f'\nRetrieving repos since {last_crawled}')
            response = retrieve_repo(page)
            repos = response['items']
            number_of_repositories = response['total_count']
            # //.items
            for name, ident in list(map(lambda repo: (repo['full_name'], repo['id']), repos)):

                print(f'>>> {ident} - {name}')
                repos_crawled += 1
                last_crawled = ident

                wait()
                langs = retrieve_languages(name)

                wait()
                commits = retrieve_commits(name)

                repo_dict = {'repository': name,
                             'languages': langs,
                             'commits': commits}
                with open(repos_filename, 'a+', encoding='utf8') as file:
                    if repos_crawled > 1:
                        file.write(',\n')
                    file.write(json.dumps(repo_dict, ensure_ascii=False))
            wait()
        except CrawlerException as e:
            repos_crawled += 1
            print(e)
        page += 1
        


def main():
    global basicAuthCredentials
    try:
        os.mkdir('files')
    except OSError:
        pass

    with open(credentials_filename, 'r') as cred:
        credentials = json.load(cred)
        username = credentials['username']
        password = credentials['password']
        token = credentials['token']
        if not username or not password:
            print('Please enter your GitHub credentials in the file credentials.json to start crawling.')
            exit()
        basicAuthCredentials = (token)

    atexit.register(close_file)
    crawl_repos()


if __name__ == "__main__":
    main()
