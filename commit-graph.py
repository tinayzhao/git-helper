import dash
import dash_core_components as dcc
import dash_html_components as html
import networkx as nx
import plotly.graph_objs as go

import pandas as pd
from colour import Color
from datetime import datetime
from textwrap import dedent as d
import json
import math
from git import *
import os
import time
import numpy as np

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app.title = "Git Visualizer"

COMMIT = 1
HEAD = 1

with open("repo.txt", "r") as f:
    repo_path = f.read()
    repo = Repo(repo_path)

commits = pd.read_csv('commits.csv')
edges = pd.read_csv('edges.csv')

headNode = []
for commit in commits.iterrows():
    if commit[1]['is_head']:
        headNode = commit[1]

def get_hovertext(commit):
    commit_msg = commit["commit_msg"]
    commit_sha = commit["commit_sha"]
    filenames = []
    for blob in repo.commit(commit_sha).tree.blobs:
        filenames.append(blob.name)

    tag = commit["tag"]

    result = f"Message: {commit_msg}<br>"
    result += f"Tag: {tag}<br>"
    result += "Filenames present:"
    for filename in filenames:
        result += f" {filename}"

    return result


def get_node_positions(commits_df):
    df = commits_df
    df['pos'] = ''
    branchX = {}
    branchY = {}
    childToParent = dict(zip(edges['child_sha'], edges['parent_sha']))
    earliestTime = min(commits['timestamp'])
    nextBranchHeight = 0
    nodePos = {}
    for row in df.iterrows():
        commit = row[1]['commit_sha']
        branch = row[1]['branch']
        if (row[1]['timestamp'] == earliestTime):
            parent = ""
        else:
            parent = childToParent[commit]    
        if (branch not in branchX):
            if parent != "": ### work here
                branchX[branch] = nodePos[parent][0] + .25
            else:
                branchX[branch] = 0
            branchY[branch] = nextBranchHeight
            if (nextBranchHeight > 0):
                nextBranchHeight = -nextBranchHeight
            else:
                nextBranchHeight = -nextBranchHeight + 1
        else:
            branchX[branch] += .5
        nodePos[commit] = [branchX[branch], branchY[branch]]

    return nodePos

def commit_graph(edges1, commits1):
    edges_df = edges1
    commits_df = commits1
    commitsList = commits1['commit_sha']
    source = edges_df['parent_sha']
    target = edges_df['child_sha']


    G = nx.from_pandas_edgelist(edges_df, 'child_sha', 'parent_sha', create_using=nx.MultiDiGraph())
    nx.set_node_attributes(G, commits_df.set_index('commit_sha')['commit_msg'].to_dict(), 'commit_msg')
    nx.set_node_attributes(G, pd.Series(commits_df.commit_sha.values,index=commits_df.commit_sha.values).to_dict(), "commit_sha")
    nx.set_node_attributes(G, commits_df.set_index('commit_sha')['tag'].to_dict(), 'tag')

    nodePositions = get_node_positions(commits)
    
    labels = {} 
    headerPositions = {}
    for node in nodePositions:
        G.nodes[node]['pos'] = nodePositions[node]
        if node == headNode['commit_sha']:
            labels[node] = 'HEAD'
        else:
            labels[node] = ''
        headerPositions[node] = np.add(nodePositions[node], [0, .3])
    traceRecode = []
    colors = list(Color('lightcoral').range_to(Color('darkred'), len(G.edges())))
    colors = ['rgb' + str(x.rgb) for x in colors]
    index = 0
    
    for edge in G.edges:
        x0, y0 = G.nodes[edge[0]]['pos']
        x1, y1 = G.nodes[edge[1]]['pos']
        trace = go.Scatter(x=tuple([x0, x1, None]), y=tuple([y0, y1, None]),
                           mode='lines',
                           marker=dict(color=colors[index]),
                           line_shape='spline',
                           opacity=1)
        traceRecode.append(trace)
        index = index + 1
    node_trace = go.Scatter(x=[], y=[], hovertext=[], text=[], mode='markers+text', textposition="bottom center",
                            hoverinfo="text", marker = {'size': 50}, fillcolor='chocolate')

    index = 0
    for node in G.nodes():
        x, y = G.nodes[node]['pos']
        hovertext = get_hovertext(G.nodes[node])
        text = G.nodes[node]["commit_sha"][:4] + "..." + labels[node]
        node_trace['x'] += tuple([x])
        node_trace['y'] += tuple([y])
        node_trace['hovertext'] += tuple([hovertext])
        node_trace['text'] += tuple([text])
        index = index + 1
    traceRecode.append(node_trace)
    middle_hover_trace = go.Scatter(x=[], y=[], hovertext=[], mode='markers+text', hoverinfo="text",
                                    marker={'size': 20, 'color': 'LightSkyBlue'},
                                    opacity=0)

    ###################################
    index = 0
    for edge in G.edges:
        x0, y0 = G.nodes[edge[0]]['pos']
        x1, y1 = G.nodes[edge[1]]['pos']
        middle_hover_trace['x'] += tuple([(x0 + x1) / 2])
        middle_hover_trace['y'] += tuple([(y0 + y1) / 2])
        index = index + 1

    traceRecode.append(middle_hover_trace)


    ###################################
    figure = {
            "data": traceRecode,
            "layout": go.Layout(title='Git Visualization', showlegend=False, hovermode='closest',
                                margin={'b': 40, 'l': 40, 'r': 40, 't': 40},
                                xaxis={'showgrid': False, 'zeroline': False, 'showticklabels': False},
                                yaxis={'showgrid': False, 'zeroline': False, 'showticklabels': False},
                                height=600,
                                clickmode='event+select',
                                annotations=[
                                    dict(
                                        ax=(G.nodes[edge[0]]['pos'][0] + G.nodes[edge[1]]['pos'][0]) / 2,
                                        ay=(G.nodes[edge[0]]['pos'][1] + G.nodes[edge[1]]['pos'][1]) / 2, axref='x', ayref='y',
                                        x=(G.nodes[edge[1]]['pos'][0] * 3 + G.nodes[edge[0]]['pos'][0]) / 4,
                                        y=(G.nodes[edge[1]]['pos'][1] * 3 + G.nodes[edge[0]]['pos'][1]) / 4, xref='x', yref='y',
                                        showarrow=True,
                                        arrowhead=3,
                                        arrowsize=4,
                                        arrowwidth=1,
                                        opacity=1
                                    ) for edge in G.edges]
                                )}
    return figure

# styles: for right side hover/click component
styles = {
    'pre': {
        'border': 'thin lightgrey solid',
        'overflowX': 'scroll'
    }
}

app.layout = html.Div([
    #####################
    html.Div([html.H1("Git Visualizer")],
        className="row",
        style = {'textAlign': "center"}),
    #####################################
    html.Div(
        dcc.Markdown('''
        #### How Git Visualizer works 

        Git Visualizer is for people who are new to git and would like some visual intuition behind some of
        the commands they run. You can run Git Visualizer on any git repository you have and it displays 
        relevant information like branches, commit shas, tags, and can even help visualize merges.

        You may also create tags for any commit through our interface as well as merge into your current
        branch.
        ''')
    ),
    html.Div(
        className='graph',
        children=[dcc.Graph(id="my-graph", 
            figure = commit_graph(edges, commits))],
    ),
    #####
    html.Div(
        children = [
        html.Div(dcc.Input(id='input-box', type='text')),
        html.Button('Submit', id='button'),
        html.Div(id='output-container-button',
            children=['Enter the first 4 digits of the commit sha id followed by a space and then your tag label'])
        ]

        )
    ]
)


@app.callback(
    dash.dependencies.Output('my-graph', 'figure'),
    [dash.dependencies.Input('my-graph', 'clickData'),
    dash.dependencies.Input('button', 'n_clicks')],
    [dash.dependencies.State('input-box', 'value')])
def update_figure(clickData, n_clicks, value):
    file = open('repo.txt', 'r')
    repoPath = file.read()
    repo = Repo(repoPath)
    msg = ""
    commits = pd.read_csv('commits.csv')
    edges = pd.read_csv('edges.csv')
    if clickData:
        commitID = clickData['points'][0]['text'][0:4]
        try:
            repo.git.merge(commitID)
            msg = "git merge " + commitID
            os.system("python3 parser.py " + repoPath)

            commits = pd.read_csv('commits.csv')
            edges = pd.read_csv('edges.csv')
            print('Merge Successful')
        except:
            print("Unable to merge " + commitID)
    if (value is not None and len(value) >= 4):
        try:
        	split = value.split(" ")
        	assert len(split) == 2, "bad tag name"
        	sha, tag = split
        	repo.create_tag(tag, sha)
        	os.system(f"python3 parser.py {repoPath}")
        	commits = pd.read_csv('commits.csv')
        	edges = pd.read_csv('edges.csv')
        	print('Tag Success')
        except:
        	print("Unable to tag " + value)
        
    return
   

    


app.run_server(debug=True)
