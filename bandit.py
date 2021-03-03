import numpy as np
import random
import matplotlib as mpl
import matplotlib.pyplot as plt
mpl.use('tkagg')

PLAY_CNT = 1000     # プレイ回数

def greedy(epsilon):
    rewardsList = np.empty((0, PLAY_CNT), int)  # 1000回分の報酬*2000回の施行
    for j in range(2000):
        QaActuals = np.random.randn(10)     # Qaの報酬の期待値
        r = [[],[],[],[],[],[],[],[],[],[]]     # アームaを選択したときの報酬リスト
        QaEstimates = [0]*10    # Qaの報酬の期待値の推定値
        rewards = []    # 1000回分の報酬

        for i in range(PLAY_CNT):
            a=0
            if epsilon < random.random():
                QaEstimatesMaxIndexs = [i for i, v in enumerate(QaEstimates) if v == max(QaEstimates)]
                a = random.choice(QaEstimatesMaxIndexs)     # 推定値が高いアーム
            else:
                a = random.randint(0, 9)    # ランダムに選択したアーム
                
            li = np.random.normal(QaActuals[a], 1, 1)   # aの報酬
            reward = li[0]
            (r[a]).append(reward)
            rewards.append(reward)
            raLen = len(r[a])
            QaEstimate = (QaEstimates[a]*(raLen-1) + reward)/raLen  # Qa算出（計算コストの高いsum関数は使わず工夫）
            QaEstimates[a] = QaEstimate
            
        rewardsList = np.append(rewardsList, np.array([rewards]), axis=0)
        print(j)
    
    return rewardsList

epsilons = [0, 0.01, 0.1]   # グリーディ手法、εグリーディ手法（ε=0.01, 0.1）
labels = []     # グラフの凡例
for epsilon in epsilons:
    if epsilon == 0:
        labels.append("Greedy")
    else:
        labels.append("ε = {}".format(epsilon))

for epsilon in epsilons:
    rewardsList = greedy(epsilon)
    rewardsMeans = rewardsList.mean(axis=0) # 2000回分の平均
    x = list(range(len(rewardsMeans)))
    plt.plot(x, rewardsMeans, label = labels.pop(0))
    
plt.xlabel('Plays')
plt.ylabel('Average reward')
plt.ylim(bottom=0)
plt.legend(loc=0)
plt.show()
