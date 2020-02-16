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

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app.title = "Git Visualizer"

COMMIT = 1
HEAD = 1

commits = pd.read_csv('commits.csv')
edges = pd.read_csv('edges.csv')


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

def commit_graph(CommitToSearch, commits_df, edges_df):
	#edges_df = self.e
	#commits_df = self.commits
	commitsList = commits_df['commit_sha']
	source = edges_df['parent_sha']
	target = edges_df['child_sha']
	print("inside commit_graph")
	print(edges_df)
	print(commits_df)
	shells = []
	shell1=[]
	shell1.append(CommitToSearch)
	shells.append(shell1)
	shell2=[]
	for commit in commitsList:
		if commit!=CommitToSearch:
			shell2.append(commit)
	shells.append(shell2)

	G = nx.from_pandas_edgelist(edges_df, 'child_sha', 'parent_sha', create_using=nx.MultiDiGraph())
	nx.set_node_attributes(G, commits_df.set_index('commit_sha')['commit_msg'].to_dict(), 'commit_msg')
	nx.set_node_attributes(G, pd.Series(commits_df.commit_sha.values,index=commits_df.commit_sha.values).to_dict(), "commit_sha")


	if len(shell2) > 1:
		pos = nx.layout.shell_layout(G, shells)
	else: 
		pos = nx.layout.spring_layout(G)

	nodePositions = get_node_positions(commits)
	
	for node in nodePositions:
		G.nodes[node]['pos'] = nodePositions[node]


	if len(shell2)==0:
		traceRecode = []  # contains edge_trace, node_trace, middle_node_trace
		node_trace = go.Scatter(x=tuple([1]), y=tuple([1]), text=tuple([str(AccountToSearch)]), textposition="bottom center",
                                mode='markers+text',
                                marker={'size': 50, 'color': 'LightSkyBlue'})
		traceRecode.append(node_trace)
		node_trace1 = go.Scatter(x=tuple([1]), y=tuple([1]),
                                mode='markers',
                                marker={'size': 50, 'color': 'LightSkyBlue'},
                                opacity=0)
		traceRecode.append(node_trace1)
		figure = {
            "data": traceRecode,
            "layout": go.Layout(title='Git Visualizer', showlegend=False,
                                margin={'b': 40, 'l': 40, 'r': 40, 't': 40},
                                xaxis={'showgrid': False, 'zeroline': False, 'showticklabels': False},
                                yaxis={'showgrid': False, 'zeroline': False, 'showticklabels': False},
                                height=600
                                )}
		return figure
	traceRecode = []
	colors = list(Color('lightcoral').range_to(Color('darkred'), len(G.edges())))
	colors = ['rgb' + str(x.rgb) for x in colors]
	index = 0
	
	for edge in G.edges:
		print(G.nodes[edge[0]])
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
                            hoverinfo="text", marker={'size': 50, 'color': 'LightSkyBlue'})
	index = 0
	for node in G.nodes():
		x, y = G.nodes[node]['pos']
		hovertext = "Commit Message: " + str(G.nodes[node]['commit_msg'])
		text = G.nodes[node]["commit_sha"][:4] + "..." 
		node_trace['x'] += tuple([x])
		node_trace['y'] += tuple([y])
		node_trace['hovertext'] += tuple([hovertext])
		node_trace['text'] += tuple([text])
		index = index + 1
	traceRecode.append(node_trace)
	middle_hover_trace = go.Scatter(x=[], y=[], hovertext=[], mode='markers', hoverinfo="text",
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


app.layout = html.Div([
	#####################
	html.Div([html.H1("Git Visualizer")],
		className="row",
		style = {'textAlign': "center"}),
	#####################################
	html.Div(
		className="row",
		children=[
		##################################
			html.Div(
				className='checklist',
				children=[
				dcc.Markdown(d("""
					**Check data**

                    Look at this data.
                    """)),
				dcc.Input(id="input1", type="text",placeholder="Commit #"),
				html.Div(id="output")
			],
			style = {'height': '300px'}
			)#,
			#html.Div(
			#	className='gitcommand',
			#	children=[
			#	dcc.Input(id="input2", type="text",placeholder="Command")
			#	]
			#)
		]
	),
	html.Div(
		className='graph',
		children=[dcc.Graph(id="my-graph", 
			figure = commit_graph(COMMIT, commits, edges))],
	),
	#####
	html.Div(
		className = "right"
		)
	]
)


@app.callback(
    dash.dependencies.Output('my-graph', 'figure'),
   # dash.dependencies.Output('git-command', 'value'),
    [dash.dependencies.Input('my-graph', 'clickData')])
def update_figure(clickData):
    file = open('repo.txt', 'r')
    repoPath = file.read()
    repo = Repo(repoPath)
    msg = ""
    commits = pd.read_csv('commits.csv')
    edges = pd.read_csv('edges.csv')
    if clickData:
        commitID = clickData['points'][0]['text'][0:4]
        print(commitID)
        try:
            repo.git.merge(commitID)
            print("did command")
            msg = "git merge " + commitID
            print(msg)
            os.system("python3 parser.py " + repoPath)
            time.sleep(10)
            commits = pd.read_csv('commits.csv')
            edges = pd.read_csv('edges.csv')
           # print(commits)
           # print(edges)
           # app.run_server(debug=True)	
        except:
            msg = "Unable to merge " + commitID
            print(msg)
    return commit_graph(COMMIT, commits, edges)
    #, msg
   

if __name__ == "__main__":
	app.run_server(debug=True)			
					
				


		
