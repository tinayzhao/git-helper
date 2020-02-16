""" Creates two CSVs that represent the graph of the N most recent commits. 

Use as follows:


    python parser.py <insert path to git repository here> <number of commits here>

    If you want to create the csv over the current git repository, insert "." for the path

"""

from git import *
import csv
import sys


""" Returns a List of String filenames from the given Commit object. """
def get_blob_names_of_commit(commit_obj):
    tree = commit_obj.tree
    blob_names = []
    for blob in tree.blobs():
        blob_names.append(blob.name)
    return blob_name


""" Returns (1) a Dictionary of the N most recent Commit objects keyed by name of branch and
            (2) a List of Edges of the N most recent commits of REPO on the current branch. 

    Edges are in the form: (child, parent) to denote that PARENT has a directed edge to CHILD

    Here is an example with no merges:

           C - D      OTHER 
          /     
    A - B - E - F     MASTER
                ^
                |

    Where the HEAD pointer is at commit F. Note that commits D and C don't matter in this case. Say N = 4.

    The Dictionary of Commit objects we will return is:

    { "MASTER" : [F, E, B, A] }

    and the list of Edges will be:
    [
        [F, E],
        [E, B],
        [B, A]
    ]


    Here is an example with a merge:

          C - D     OTHER 
         /     \
    A - B - E - F   MASTER
                ^
                |

    Where the HEAD pointer is at commit F. If we want the 5 most recent commits, we'll return this:

    If N = 5, the Dictionary of Commit objects we'll return is:
    { "MASTER" : [F, E, B], "OTHER" : [D, C]" }

    and the list of Edges will be:

    [
        [F, D],
        [F, E],
        [D, C],
        [E, B],
        [C, B]
    ]

"""
def n_most_recent_commits(repo, n):

    """ Gets the most recent commit and its branch name. """
    queue = [ (repo.active_branch.name, repo.commit()) ]
    """ Already added the most recent commit. """
    i = 1
    commits = {} 
    edges = []
    for branch_name, commit in queue:
        if branch_name not in commits:
            commits[branch_name] = [commit]
        else:
            commits[branch_name].append(commit)

        is_merge = len(commit.parents) > 1
        for parent_commit in commit.parents:
            """ Done adding commits. """
            if i == n:
                break
            if is_merge:
                for branch in repo.branches:
                    if branch.commit == parent_commit:
                        queue.append( (branch.name, parent_commit) )
                        break
            else:
                queue.append( (branch_name, parent_commit) )

            edges.append( (commit, parent_commit) )
            i += 1
    return commits, edges


""" Creates a dictionary from the commit to fit the columns of commits.csv as described in the 
    export_to_csv function below. """
def commit_to_dict(branch_name, commit):
    d = {}
    d["commit_sha"] = commit.hexsha
    d["commit_msg"] = commit.summary
    d["timestamp"]  = commit.authored_date
    d["branch"]     = branch_name 
    d["is_head"]    = commit.repo.commit() == commit
    d["is_head_of_branch"] = any([commit == b.commit for b in commit.repo.branches])
    d["tag"] = ""

    for tag in commit.repo.tags:
        if tag.commit == commit:
            d["tag"] = tag.name
    return d


""" 
    Writes the COMMITS and EDGES to two csv's labeled 'commits.csv' and 'edges.csv' as described below:

    
    commits.csv has the following columns:
    commit_sha, commit_msg, timestamp, tag, branch, is_head, is_head_of_branch

    where is_head and is_head_of_branch will be either 'True' or 'False'

    edges.csv has the following columns:
    child_sha, parent_sha

"""
def export_to_csv(commits_by_branch, edges):
    commit_columns = ["commit_sha", "commit_msg", "timestamp", "tag", \
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


if __name__ == "__main__":

    if len(sys.argv) != 3:
        print("please provide the path of the git repository and the number of commits to include")
    else:
        repo = Repo(sys.argv[1])
        n = sys.argv[2]

        commits, edges = n_most_recent_commits(repo, n)

        export_to_csv(commits, edges)

