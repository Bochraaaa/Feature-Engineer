
import pandas as pd
import numpy as np
import gc
from sklearn.model_selection import KFold, GroupKFold
from xgboost import XGBClassifier
from sklearn.metrics import f1_score, make_scorer
from tqdm import tqdm
from sklearn.model_selection import RandomizedSearchCV

data = pd.read_csv("/kaggle/input/predict-student-performance-from-game-play/train.csv",usecols=[0])

data = data['session_id'].groupby(data['session_id']).count()
PIECES = 10
CHUNK = int( np.ceil(len(data)/PIECES) )
reads = []
skips = [0]
for k in range(PIECES):
    a = k*CHUNK
    b = (k+1)*CHUNK
    if b>len(data): b=len(data)
    r = data.iloc[a:b].sum()
    reads.append(r)
    skips.append(skips[-1]+r)
print(f'To avoid memory error, we will read train in {PIECES} pieces of sizes:')
print(reads)

train = pd.read_csv('/kaggle/input/predict-student-performance-from-game-play/train.csv', nrows=reads[0])
print('Train size of first piece:', train.shape )
train.head()

labels = pd.read_csv('/kaggle/input/predict-student-performance-from-game-play/train_labels.csv')
labels['session'] = labels.session_id.apply(lambda x: int(x.split('_')[0]) )
labels['q'] = labels.session_id.apply(lambda x: int(x.split('_')[-1][1:]) )
print( labels.shape )
labels.head()

CATS = ['event_name', 'fqid', 'room_fqid', 'text_fqid', 'text', 'name']
NUMS = ['elapsed_time','level','page','room_coor_x', 'room_coor_y',
        'screen_coor_x', 'screen_coor_y','hover_duration']
EVENTS = ['navigate_click','person_click','cutscene_click','object_click',
          'map_hover','notification_click','map_click','observation_click',
          'checkpoint']

def feature_engineer(train):

    dfs = []
########categorical###############
    for c in CATS:
        tmp = train.groupby(['session_id','level_group'])[c].agg('nunique')
        tmp.name = tmp.name + '_nunique'
        dfs.append(tmp)
###############nums###############
    for c in NUMS:
        tmp = train.groupby(['session_id','level_group'])[c].agg('mean')
        tmp.name = tmp.name + '_mean'
        dfs.append(tmp)
    for c in NUMS:
        tmp = train.groupby(['session_id','level_group'])[c].agg('std')
        tmp.name = tmp.name + '_std'
        dfs.append(tmp)
    for c in NUMS:
        tmp = train.groupby(['session_id', 'level_group'])[c].agg(lambda x: x.max() - x.min())
        tmp.name = tmp.name + '_range'
        dfs.append(tmp)
    for c in NUMS:
        tmp = train.groupby(['session_id', 'level_group'])[c].agg('median')
        tmp.name = tmp.name + '_median'
        dfs.append(tmp)

##############EVENTS list###################""
    for c in EVENTS:
        train[c] = (train.event_name == c).astype('int8')
    for c in EVENTS + ['elapsed_time']:
        tmp = train.groupby(['session_id','level_group'])[c].agg('sum')
        tmp.name = tmp.name + '_sum'
        dfs.append(tmp)
    for c in EVENTS :
        tmp = train.groupby(['session_id', 'level_group'])[c].agg(lambda x: x.mode().values[0])
        tmp.name = tmp.name + '_mode'
        dfs.append(tmp)



    train = train.drop(EVENTS,axis=1)
    df = pd.concat(dfs,axis=1)
    df = df.fillna(-1)
    df = df.reset_index()
    df = df.set_index('session_id')
    return df

