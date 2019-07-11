import unicodedata
import json
import re


def process_commits(commits):
    good_commits = []
    for commit in commits:
        # filter out invalid commits
        if len(re.findall(r'[\u4e00-\u9fff]+', commit)) > 0:
            continue  # don't include commits with chinese characters
        if len(re.findall('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+',
                          commit)) > 0:
            continue  # don't include commits with links
        if len(re.findall(r'\S+@\S+.', commit)) > 0:
            continue  # don't include commits with e-mail addresses
        if 'asd' in commit or 'initial commit' in commit:
            continue

        commit = commit.strip()  # remove trailing spaces
        commit = "".join(ch for ch in commit if unicodedata.category(ch)[0] != "C")  # remove control characters

        if len(commit) < 5:
            continue  # don't include very short commit messages

        good_commits.append(commit)
    return good_commits


def get_relevant_langs(languages):
    relevant_languages = []
    total = 0.0
    num_languages = len(languages.keys())
    for lang in languages.keys():
        total += languages[lang]
    for lang in languages.keys():
        if languages[lang] >= total / num_languages:
            relevant_languages.append(lang)
    return relevant_languages


def main():
    unique_repos = []
    features = []
    labels = []
    with open('files/repos.json', encoding='utf8') as file:
        repos = json.load(file)
        for repo in repos:
            name = repo["repository"]
            if name in unique_repos:
                continue
            else:
                unique_repos.append(name)

            languages = get_relevant_langs(repo["languages"])
            commits = process_commits(repo["commits"])

            # print(f'Name: {name}')
            # print(f'Languages: {languages}')
            # print(f'Commits: {commits}')
            # print()

            if len(languages) == 0 or len(commits) < 5:
                continue

            for commit in commits:
                features.append(commit)
                labels.append(languages)

    if len(features) != len(labels):
        print('Unequal amount of features and labels. Something went horribly wrong')

    print(f'{len(features)} feature extracted')
    print(f'{len(labels)} feature extracted')

    with open('files/features.json', 'w') as file:
        file.write(json.dumps(features))

    with open('files/labels.json', 'w') as file:
        file.write(json.dumps(labels))


if __name__ == "__main__":
    main()
