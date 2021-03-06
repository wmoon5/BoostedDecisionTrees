import numpy as np
import pandas as pd


# specific to MITF-Myc project

def OnevAll_SplitTrainTest(df, signal, TF_list):
    if len(df[df.which==signal]) > df.which.value_counts().min()*3:
        training_num = df.which.value_counts().min()*2
        test_num = df.which.value_counts().min()
    else:
        training_num = int(len(df[df.which==signal])*.666)
        test_num = len(df[df.which==signal]) - training_num
        
    train_rows_signal = np.random.choice(df[df.which==signal].index.values, training_num, replace=False)
    train_rows_background = []
    for i in [x for x in TF_list if x != signal]:
        train_rows_background = np.append(train_rows_background,
                                          np.random.choice(df[df.which==i].index.values, training_num*.333, replace=False))
    
    test_rows_signal = np.random.choice(df[df.which==signal].drop((train_rows_signal)).index.values, test_num, replace=False)
    test_rows_background = []
    for i in [x for x in TF_list if x != signal]:
        test_rows_background = np.append(test_rows_background, 
                                        np.random.choice(df.drop((train_rows_background))[df.drop((train_rows_background)).which==i].index.values,
                                        test_num*.333, replace=False))
    df_train = df.ix[np.hstack((train_rows_signal, train_rows_background))]
    df_test = df.ix[np.hstack((test_rows_signal, test_rows_background))]
    
    return df_train, df_test



#scikit-learn and BDT-specific functions

def get_importances_dict(bdt, branch_names):
    importances = bdt.feature_importances_
    indices = np.argsort(importances)[::-1]
    importances_dict = {}
    for i in range(len(branch_names)):
        importances_dict[branch_names[indices[i]]] = i
    return importances_dict

def order_by_importance(bdt, branch_names):
    importances = bdt.feature_importances_
    indices = np.argsort(importances)[::-1]
    importances_list = []
    for i in range(len(branch_names)):
        importances_list.append(branch_names[indices[i]])
    return importances_list

def find_depths_in_tree(feature_index, tree):
    depths_in_tree = []
    left_children = list(tree.tree_.children_left)
    right_children = list(tree.tree_.children_right)

    for i in np.where(tree.tree_.feature == feature_index)[0]:
        index = i
        count = 0
        while index != 0:
            if index in left_children:
                index = left_children.index(index)
                count += 1
                #print "left"
            elif index in right_children:
                index = right_children.index(index)
                count += 1
                #print "right"
            else:
                print "something's wrong..."
                index = 0

        #print count
        depths_in_tree.append(count)
    return depths_in_tree

def find_all_depths(feature_index, BDT):
    all_depths = []
    for tree in BDT.estimators_:
        all_depths += find_depths_in_tree(feature_index, tree)
    return all_depths




## working with Graphs

#def add_information_from_tree(tree, matrix, weight=1):
#    zipped = zip(tree.children_left, tree.children_right, tree.feature, tree.threshold)
#    for i in range(len(zipped)):
#        if zipped[zipped[i][0]][2] < 0:
#            pass
#        else:
#            parent = zipped[i][2]
#            left_child = zipped[zipped[i][0]][2]
#            right_child = zipped[zipped[i][1]][2]
# 
#            matrix[parent][left_child] += weight
#            matrix[parent][right_child] += weight
#    
#    return matrix

def add_information_from_tree(tree, matrix, weight=1):
    zipped = zip(tree.children_left, tree.children_right, tree.feature, tree.threshold)
    for i in range(len(zipped)):

        parent = zipped[i][2]
        left_child = zipped[zipped[i][0]][2]
        right_child = zipped[zipped[i][1]][2]
 
        if left_child >= 0:
            matrix[parent][left_child] += weight
        if right_child >= 0:
            matrix[parent][right_child] += weight
    
    return matrix

def get_directed_matrix(bdt, branch_names, weighted=False):
    connections = np.zeros((len(branch_names), len(branch_names)))
    if weighted:
        for i in range(len(bdt.estimators_)):
            connections = add_information_from_tree(bdt.estimators_[i].tree_, connections, weight = bdt.estimator_weights_[i])
    else:
        for tree in bdt.estimators_:
            connections = add_information_from_tree(tree.tree_, connections)
    return connections

def get_undirected_matrix(bdt, branch_names, weighted=False):
    connections = get_directed_matrix(bdt, branch_names, weighted)
    for i in range(len(connections)):
        for j in range(i):
            connections[i][j] += connections[j][i]
            connections[j][i] = 0
    return connections


def remove_edgeless(graph):
    degree_dict = graph.degree()
    to_keep = [x for x in degree_dict if degree_dict[x] > 0]
    return graph.subgraph(to_keep)




