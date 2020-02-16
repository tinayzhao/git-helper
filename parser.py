""" Creates two CSVs that represent the history of commits via graph. 

Use as follows:


    python parser.py <insert path to git repository here>

    If you want to create the csv over the current git repository, insert "." for the path

"""

from git import *
import csv
import sys
import operator
import pandas as pd




def update_commits(commits, history1, history2, branch1, branch2, head1, head2, visited):
    visited1 = set([c.hexsha for c in history1])

    for c in history1:
        if c.hexsha not in visited:
            commits[branch1.name].append(c)
            visited.add(c.hexsha)

    for c in history2:
        if c.hexsha not in visited:
            visited.add(c.hexsha)
            if c not in visited1:
                commits[branch2.name].append(c)

    


""" COMMIT is the result of a merge. Updates dictionaries accordingly """
def mark_levels_from_merge(commit, visited_commit_shas, commit_to_level, edges):
    level = commit_to_level[commit]
    commit_to_level[commit.parents[0]] = level
    commit_to_level[commit.parents[1]] = level + 1

    for parent in commit.parents:
        visited_commit_shas.add(parent.hexsha)
        edges.append( (commit, parent) )

    stack = [commit.parents[0], commit.parents[1]]
    while stack != []:
        commit = stack.pop()

        if len(commit.parents) == 2:
            mark_levels_from_merge(commit, visited_commit_shas, commit_to_level)
        elif len(commit.parents) == 1:
            parent = commit.parents[0]
            if parent.hexsha in visited_commit_shas:
                continue
            else:
                commit_to_level[parent] = commit_to_level[commit]
                edges.append( (commit, parent) )

            


""" Returns (1) a Dictionary all the Commit objects keyed by name of branch and
            (2) a List of Edges of all the Commits of REPO on the current branch. 

    Edges are in the form: (child, parent) to denote that PARENT has a directed edge to CHILD

    Here is an example with no merges:

           C - D      OTHER 
          /     
    A - B - E - F     MASTER
                ^
                |

    Where the HEAD pointer is at commit F. 

    The Dictionary of Commit objects we will return is:

    { "MASTER" : [F, E, B, A], "OTHER" : [D, C] }

    and the list of Edges will be:
    [
        [F, E],
        [E, B],
        [B, A],
        [D, C],
        [C, B]
    ]


    Here is an example with a merge:

          C - D     OTHER 
         /     \
    A - B - E - F   MASTER
                ^
                |

    Where the HEAD pointer is at commit F. 

    Dictionary of Commit objects we'll return is:
    { "MASTER" : [F, E, B, A], "OTHER" : [D, C]" }

    and the list of Edges will be:

    [
        [F, D],
        [F, E],
        [D, C],
        [E, B],
        [C, B],
        [B, A]
    ]

"""
def get_commits_and_edges(repo):

    commits = {} 
    edges = []
    visited_commit_shas = set()

    """ Gets the most recent commit on each branch. """
    for branch in repo.branches:
        head = branch.commit
        commits[branch.name] = [head]
        visited_commit_shas.add(head.hexsha)

        c = head
        while len(c.parents) > 0:
            for parent in c.parents:
                edges.append( (c, parent) )
            c = c.parents[0]
            if c.hexsha not in visited_commit_shas:
                visited_commit_shas.add(c.hexsha)
                commits[branch.name].append(c)

    n = len(repo.branches)
    for i in range(n):
        for j in range(i + 1, n):
            branch1 = repo.branches[i]
            branch2 = repo.branches[j]
            head1 = branch1.commit
            head2 = branch2.commit
            history1 = [c for c in head1.traverse()]
            history2 = [c for c in head2.traverse()]

            update_commits(commits, history1, history2, branch1, branch2, head1, head2, visited_commit_shas)
    return commits, edges
"""
    visited_commit_shas = set()
    edges = []
    while stack != []:
        level, commit = queue.pop(0)
        if commit.hexsha not in visited_commit_shas:
            visited_commit_shas.add(commit.hexsha)
        else:
            continue
        if branch_name not in commits:
            commits[branch_name] = [commit]
        else:
            commits[branch_name].append(commit)

        is_merge = len(commit.parents) = 2
        if is_merge:
            mark_levels_from_merge(commit, visited_commit_shas, commit_to_level, commits, edges)
            continue
        to_add = []
        for parent_commit in commit.parents:
            if i == n:
                break
            i += 1
            if is_merge:
                found = False
                for branch in repo.branches:
                    if branch.commit == parent_commit:
                        found = True
                        to_add.append( (branch.name, parent_commit) )
                        edges.append( (commit, parent_commit) )
                        break
                if found:
                    continue
            to_add = [ (branch_name, parent_commit) ] + to_add
            edges.append( (commit, parent_commit) )
        queue.extend(to_add)
        """


""" Creates a dictionary from the commit to fit the columns of commits.csv as described in the 
    export_to_csv function below. """
def commit_to_dict(branch_name, commit):
    d = {}
    d["commit_sha"]        = commit.hexsha
    d["tree_sha"]          = commit.tree.hexsha
    d["commit_msg"]        = commit.summary
    d["timestamp"]         = commit.authored_date
    d["branch"]            = branch_name 
    d["is_head"]           = commit.repo.commit() == commit
    d["is_head_of_branch"] = any([commit == b.commit for b in commit.repo.branches])
    d["tag"]               = ""

    for tag in commit.repo.tags:
        if tag.commit == commit:
            d["tag"] = tag.name
            print(f"tag {tag.name} found for commit {commit.hexsha}")
    return d


""" 
    Writes the COMMITS and EDGES to two csv's labeled 'commits.csv' and 'edges.csv' as described below:

    
    commits.csv has the following columns:
    commit_sha, tree_sha, commit_msg, timestamp, tag, branch, is_head, is_head_of_branch

    where is_head and is_head_of_branch will be either 'True' or 'False'

    edges.csv has the following columns:
    child_sha, parent_sha

"""
def export_to_csv(commits_by_branch, edges):
    commit_columns = ["commit_sha", "tree_sha", "commit_msg", "timestamp", "tag", \
            "branch", "is_head", "is_head_of_branch"]
    with open('commits.csv', 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames = commit_columns)
        writer.writeheader()
        for branch_name in commits_by_branch:
            for commit in commits_by_branch[branch_name]:
                writer.writerow(commit_to_dict(branch_name, commit))

    with open('edges.csv', 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["child_sha", "parent_sha"])
        for edge in edges:
            writer.writerow(edge)


    """ We now sort the 'commits.csv' file by the 'timestamp' column. """
    df = pd.read_csv("commits.csv")
    df = df.sort_values(by=["timestamp"])
    df.to_csv("commits.csv", index=False)


if __name__ == "__main__":

    if len(sys.argv) != 2:
        print("please provide the path of the git repository")
    else:
        repo = Repo(sys.argv[1])

        commits, edges = get_commits_and_edges(repo)
        export_to_csv(commits, edges)
        with open("repo.txt", "w") as f:
            f.write(sys.argv[1])

