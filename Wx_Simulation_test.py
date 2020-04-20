"""
Create a 3D environment where actors will be placed in random locations with a target deck to capture actors.
The target deck will then be evaluated with Clouds to verify that they can see targets.
Clouds will have a resolution of 0.25 deg and will create a random 1 and 0 generator of place of capture of actor
whether or not actor can be seen with data taken in be NOAA weather models.
"""

import xarray as xr
import os
import rtree as rt
import pandas as pd
import numpy as np
from rtree import index
from rtree.index import Rtree
import random
import time

randomSeed = 0  # Need random seed to perform test
num_targets = 1000
num_actors = 10000

ROOT = os.getcwd()
outputFile = os.path.abspath(os.path.join(ROOT, ".."))

WxDATLocation = os.path.normpath(os.path.join(os.getcwd(), '..', 'Wx_DAT'))


def is_cloudy(self, file):
    file_df = xr.open_dataset(file)
    self.lat = file_df.latitude
    self.lon = file_df.longitude
    self.time = file_df.time
    self.vars = file_df.vars



timeEvalFile_path = os.path.join(outputFile, 'Desktop\\rtree_Stats_3D.csv')
if os.path.isfile(timeEvalFile_path):
    timeEvalFile = pd.read_csv(timeEvalFile_path)
else:
    timeEvalFile = pd.DataFrame([], columns=['NumOfTargets', 'NumOfActors', 'TimeToProcessActors (s)',
                                             'TimeToProcessScenario (s)'], index=[0])


def _build_rtree(locations):
    """ build environment of scenario using the bounded area in generate_actors """
    # Will initiate with the largest bounded area
    for location in locations['coord']:
        if location[1].startswith("Actor"):
            idx3d.insert(4444, location[0], location[1])
        else:  # id 5555 will be the box coordinates
            idx3d.insert(5555, location[0], location[1])
    return


def generate_actors(num_of_actors):
    """
    Actors are randomly generated throughout a grid of a 1000 x 1000
    Inserting a point into a rtree left == right and bottom == top

    :param num_of_actors:
    :return:
    """
    actors = dict()
    actors_loc = []
    random.seed(randomSeed)
    for i in range(num_of_actors):
        randomPoint_x, randomPoint_y, randomPoint_z = (random.uniform(0, 1000), random.uniform(0, 1000),
                                                       random.uniform(28000, 36000))
        loc = tuple([(randomPoint_x, randomPoint_y, randomPoint_x, randomPoint_y, randomPoint_z,
                      randomPoint_z), "Actor: " + str(i)])
        if not (randomPoint_x < 0) or (randomPoint_y < 0):
            actors_loc.append(loc)
        else:
            pass
        actors['coord'] = actors_loc
    return actors


def actors_in_collect(actors, targetDeck):
    """
    This will be the method to find if the actors are in our target deck
    This will have a true and false statement where if true will return the actors id and coordinates as well as which
    box, or "target deck", they are in
    """
    all_collects = []
    for i, target in targetDeck.iterrows():
        hits = list(idx3d.intersection(target['Coordinates'], objects=True))
        collected = [(target[1], item.object, tuple(item.bbox)) for item in hits]
        all_collects.append(collected)
    #
    # for actor in actors['coord']:
    #     hits = list(idx.intersection(actor[0], objects=True))
    #     collected = [(actor[1], item.object, tuple(item.bbox)) for item in hits if item.id == 5555]
    #     all_collects.append(collected)
    return all_collects


def build_tgt_deck():
    """
    build_tgt_deck generate randomly placed rectangles with varying sides on a grid of a 1000
    X and Y values less than zero will not be appended to the list of targets
    :return:
    """
    t_new = dict()
    tgt_deck = []
    random.seed(randomSeed)
    for i in range(num_targets):
        randomPoint_x, randomPoint_y = (random.uniform(0, 1000), random.uniform(0, 1000))
        width, height = (random.randint(1, 5) * 2, random.randint(1, 5) * 2)
        x_min, x_max = (randomPoint_x - width, randomPoint_x + width)
        y_min, y_max = (randomPoint_y - height, randomPoint_y + height)
        # The last two int are only used for 3D
        rect = tuple([(x_min, y_min, x_max, y_max, 0, 36000), "Location:" + str(i)])
        if not (x_min < 0) or (y_min < 0):
            tgt_deck.append(rect)
        else:
            pass
        t_new['coord'] = tgt_deck

    return t_new


# Run script here
if __name__ == '__main__':
    p = index.Property()
    p.dimension = 3
    p.dat_extension = 'data'
    p.idx_extension = 'index'
    idx3d = index.Index('3d_index', properties=p)
    # idx = index.Index(properties=p) # This is for 2D only!!!
    actors_gen = generate_actors(num_actors)
    actorScenario = pd.DataFrame(actors_gen['coord'], columns=['Coordinates', 'ActorsLocation'])
    tgt_location = build_tgt_deck()
    locs = pd.DataFrame(tgt_location['coord'], columns=['Coordinates', 'Site'])
    _build_rtree(actors_gen)
    # _build_rtree(tgt_location) # Testing to evaluate targets separately from R-tree

    # Starting time after scenario is built
    start = time.clock()

    actors_caught = actors_in_collect(actors_gen, locs)
    actorsInTargets = len(
        actors_caught)  # if multiple actors were caught in the same targeted box this will create another column
    timeProcessActors = time.clock() - start
    print("time to process %s actors and %s locations: %.03f s" % (num_actors, actorsInTargets, (timeProcessActors)))
    actors_caught = pd.DataFrame(actors_caught)
    colNames = []
    for i in range(len(actors_caught.columns)):
        colNames.append('Collections%s' % (i + 1))
    actors_caught.columns = colNames
    actors_caught = actors_caught.dropna(subset=['Collections1'])
    actors_caught = actors_caught.stack().reset_index(drop=True)
    actors_caught = pd.DataFrame(actors_caught.tolist(), columns=['Location', 'Actors', 'Coordinates'])

    new_col_list = ['left', 'bottom', 'right', 'top']
    for n, col in enumerate(new_col_list):
        actors_caught[col] = actors_caught['Coordinates'].apply(lambda location: location[n])
        locs[col] = locs['Coordinates'].apply(lambda location: location[n])
    locs = locs.drop('Coordinates', axis=1)
    actors_caught = actors_caught.drop('Coordinates', axis=1)

    actors_caught.to_csv(os.path.join(outputFile, "Desktop\\Collections3D.csv"), index=False)
    locs.to_csv(os.path.join(outputFile, "Desktop\\Target_deck3D.csv"), index=False)
    actorScenario.to_csv(os.path.join(outputFile, "Desktop\\Actors_location3D.csv"), index=False)

    # Python time.clock is deprecated, but process_time and perf_counter does not send back ns
    entireEventTime = time.clock() - start
    print("time to process whole event: %.03f s" % (entireEventTime))
    timeEvalFile_cols = timeEvalFile.columns
    timeEvalFile = timeEvalFile.append({timeEvalFile_cols[0]: num_targets, timeEvalFile_cols[1]: num_actors,
                                        timeEvalFile_cols[2]: timeProcessActors,
                                        timeEvalFile_cols[3]: entireEventTime}, True).dropna().reset_index(drop=True)
    timeEvalFile.to_csv(timeEvalFile_path, index=False)