import copy
import time
import random
from collections import deque
from collections import defaultdict
from enum import Enum
import enum
import os

# ターミナルに出力する際に、文字に色を付けるためのクラス
class Color:
    RED = '\033[31m'
    GREEN = '\033[32m'
    END = '\033[0m'
    ACCENT = '\033[01m'

# 節点を展開する関数。int型の節点を引数にして子節点のリストを返す。
def puzzleExpand(puzzleInt: int) -> list:
    puzzleList = cnvIntToList(puzzleInt)    # 節点をリストに変換
    if 0 in puzzleList:
        zeroPosi: int = puzzleList.index(0)+1   # 0(空き駒)を取得
    else:
        print("パズルに空き駒(0)が含まれていません。プログラムを中断します。\npuzzleList:{}"
              .format(puzzleList))
        exit()
    
    # 空き駒の上下左右の位置を計算
    up = zeroPosi-3
    left = zeroPosi-1
    right = zeroPosi+1
    down = zeroPosi+3
    
    # 右または左に動かしたときに、3と4、6と7の間を移動しないようにする
    if zeroPosi==3 or zeroPosi==6:
        right = 0
    elif zeroPosi==4 or zeroPosi==7:
        left = 0
    aroundPosi: list = [down, right, left, up]
    
    # パズル(3x3)の範囲外の位置を除外し、changeablePosiに保存
    changeablePosi = []
    for i in aroundPosi:
        if 1<=i<=9:
            changeablePosi.append(i)
    
    # 空き駒とchangeablePosiを交換し、リストnewPuzzlesに保存
    newPuzzles: list = []
    for i in changeablePosi:
        newPuzzleList = swap(puzzleList, i-1, zeroPosi-1)
        newPuzzleInt = cnvListToInt(newPuzzleList)
        newPuzzles.append(newPuzzleInt)
    
    return newPuzzles

# 関数searchAlgorithmの処理時間を計測し、戻り値に処理時間を追加する関数
def timeDeco(func):
    def wrapper(*args, **kwargs):
        startTime = time.time()     # 開始時間
        puzzleRoute, routeLength, searchCnt = func(*args, *kwargs)  # searchAlgorithmの戻り値を各変数に代入
        searchTime = time.time() - startTime                        # 処理時間
        print("実行時間：{0:9.6f}秒 | 処理回数：{1:6}回 | 経路長：{2}"
              .format(searchTime, searchCnt, len(puzzleRoute)))
        return {"puzzleRoute":puzzleRoute, "routeLength":routeLength,
                "searchCnt":searchCnt, "searchTime":searchTime}
    return wrapper

# 探索アルゴリズム名のenum
@enum.unique
class SearchType(Enum):
    BFS = "BFS"
    DFS = "DFS"
    ASTAR = "ASTAR"
    ALL = "ALL"

# 探索アルゴリズム関数。出発節点・目標節点・探索アルゴリズムを引数にして、得られた経路・経路長・処理回数を返す。
@timeDeco
def searchAlgorithm(START_INT: int, GOAL_INT: int, searchType: SearchType):
    
    # step1 出発節点をOpenListに入れる->要素の検索の計算コストが小さい辞書を用いる
    if searchType == SearchType.BFS or searchType == SearchType.DFS:
        openList = deque([START_INT])       # BFS,DFS用に節点のリストを作成。
    openDic = defaultdict(dict)             # 各節点を親節店(と深さとf)とともに保存するOpenListの代わりの辞書
    closedDic = defaultdict(dict)           #               〃                   ClosedListの代わりの辞書
    openDic[START_INT]["parentInt"] = -1
    if searchType == SearchType.ASTAR:      # A*アルゴリズムなら深さとfも保存
        openDic[START_INT]["depth"] = 0
        openDic[START_INT]["f"] = heuristic(START_INT, GOAL_INT)
    
    cnt = 1     # 処理回数
    while(True):
        # step2 OpenListが空なら探索失敗、終了。
        if not openDic:
            print("{0}\r探索失敗：openListが空になりました。プログラムを中断します。{1}"
                  .format(Color.RED, Color.END))
            exit()
        
        # step3 openDicから節点を取り出し、ClosedDicに追加
        if searchType == SearchType.BFS or searchType == SearchType.DFS:
            # BFSかDFSなら先頭の節点を取り出す
            puzzleInt: int = openList.popleft()
        elif searchType == SearchType.ASTAR:
            # A*ならfが最も小さい節点を取り出す
            puzzleInt: int = min(openDic.items(), key=lambda puzzleDict: puzzleDict[1]["f"])[0]
        closedDic[puzzleInt] = openDic.pop(puzzleInt)
            
        # step4 取り出した節点が目標節点なら探索は成功、終了。
        if puzzleInt == GOAL_INT:
            searchTypeValue = "<" + searchType.value + ">"
            print("{0}\r ✔ {1}探索成功 {2:7} | ".format(Color.GREEN, Color.END, searchTypeValue), end="")
            break
        
        # step5
        childInts = puzzleExpand(puzzleInt)     # 節点を展開
        
        # step5-続き (BFS,DFSの場合)
        if searchType == SearchType.BFS or searchType == SearchType.DFS:
            for childInt in childInts:
                # 子節点がopenDic,closedDicになければ
                if childInt not in openDic.keys() and childInt not in closedDic.keys():
                    openDic[childInt]["parentInt"] = puzzleInt  # openDicに子節点と親節点を保存
                    if searchType == SearchType.BFS:    # BFSなら子節点を末尾に追加
                        openList.append(childInt)
                    elif searchType == SearchType.DFS:  # DFSなら子節点を先頭に追加
                        openList.appendleft(childInt)
                    
        # step5-続き (A*の場合)
        elif searchType == SearchType.ASTAR:
            fList = []      # fのリスト
            sortedChildPuzzleInts = []
            for childInt in childInts:
                h = heuristic(childInt, GOAL_INT)   # 子節点から目標節点に至る最適経路のコストの評価値
                g = closedDic[puzzleInt]["depth"]   # 出発節店から子節点に至る最適経路のコストの評価値
                f = h + g
                childDict = {       # この子節点の辞書を作成
                    "parentInt": puzzleInt,
                    "depth": g + 1,
                    "f": f
                }
                if childInt in openDic.keys():          # 子節点と同じ配置の節点がopenDicにあり、
                    if openDic[childInt]["f"] > f:          # 子節点の方がfが小さい場合、
                        openDic[childInt] = childDict       # openDicを上書き
                elif childInt in closedDic.keys():      # 子節点と同じ配置の節点がclosedDicにあり、
                    if closedDic[childInt]["f"] > f:        # 子節点の方がfが小さい場合、
                        del closedDic[childInt]             # closedDicから削除し、
                        openDic[childInt] = childDict       # openDicに追加
                else:
                    openDic[childInt] = childDict       # どちらにもない場合そのままopenDicに追加
            
        if cnt % 100 == 0:
            print('\r{0}回目の実行'.format(cnt), end="")
        cnt += 1
        
        # step6 step2へ戻る
    
    # closedDicを使って出発節点までの経路をたどる
    childInt = GOAL_INT
    puzzleRoute = deque([childInt])     # 経路中の節点をint型で保存するリスト
    startTime = time.time()
    while(True):
        if childInt in closedDic:   # 子節点がclosedDicの中にある場合、親節点を取得
            parentInt = closedDic[childInt]["parentInt"]
            if parentInt == -1:     # 親節点が出発節点なら経路探索成功
                break
            puzzleRoute.appendleft(parentInt)   # 経路リストに親節点を追加
            childInt = parentInt                # 子節点<-親節点
        else:
            print("{0}経路が見つかりませんでした。プログラムを中断します。{1}"
                  .format(Color.RED, Color.END))
            exit()
        if time.time() - startTime > 5:     # 経路探索に5秒以上かかった場合タイムアウトする。
            print("{0}開始時のパズルまでの経路を見つからないためタイムアウトしました。プログラムを中断します。{1}"
                  .format(Color.RED, Color.END))
            exit()

    return puzzleRoute, len(puzzleRoute), cnt

# A*アルゴリズムのヒューリスティック値を取得する関数
def heuristic(puzzleInt: int, GOAL_INT: int) -> int:
    puzzleList = cnvIntToList(puzzleInt)    # 2節点ともリスト化
    goalList = cnvIntToList(GOAL_INT)
    
    h1 = 0      # ヒューリスティック値1：正しい位置に置かれていない駒の数
    for i in range(len(puzzleList)):
        if puzzleList[i] == 0:      # 空き駒は非対象
            continue
        if puzzleList[i] != goalList[i]:    # 位置が正しくない場合＋1
            h1 += 1
    
    h2 = 0      # ヒューリスティック値2：各駒の現在位置と正しい位置の間の距離の総和
    for i in range(1, len(puzzleList)):
        puzzleRow = puzzleList.index(i) // 3    # 2節点の行と列を求める
        puzzleCol = puzzleList.index(i) % 3
        goalRow = goalList.index(i) // 3
        goalCol = goalList.index(i) % 3
        h2 += abs(puzzleRow - goalRow)      # 横方向・縦方向の距離を取得し、h2に加算
        h2 += abs(puzzleCol - goalCol)
        
    return h1 + h2

# 長さ9のパズルリストを9桁のint型に変換する関数
def cnvListToInt(li: list) -> int:
    num = 0
    for i in li:
        num = num * 10 + i
    return num

# int型の9桁のパズルをリストに変換する関数
def cnvIntToList(num: int) -> list:
    li = []
    for i in range(9):
        li.insert(0, num % 10)
        num = num // 10
    return li
    
# リストの2要素を入れ替えたリストを返す関数
def swap(tmp: list, index1: int, index2: int) -> list:
    li = copy.deepcopy(tmp)
    li[index1], li[index2] = li[index2], li[index1]
    return li
    
# 解くことが可能な8パズルを作成する関数
def makePuzzle(GOAL_INT: int) -> int:
    goal = cnvIntToList(GOAL_INT)   # 完成形をリスト化
    goal[goal.index(0)] = 9         # 0を9に変えておく
    start = copy.deepcopy(goal)     # 開始形を作成
    
    # シャッフルして、それが解ける配置なのか調べる、を繰り返す
    while(True):
        random.shuffle(start)       # パズルをシャッフルする
        copyStart = copy.deepcopy(start)
        cnt = 0
        
        # 空き駒の最短距離を計算
        startRow = start.index(9) // 3    # 9の位置（行・列）を求める
        startCol = start.index(9) % 3
        goalRow = goal.index(9) // 3
        goalCol = goal.index(9) % 3
        zeroDistance = abs(startRow - goalRow)      # 横方向・縦方向の距離を取得し、zeroDistanceに加算
        zeroDistance += abs(startCol - goalCol)
            
        # startをgoalにするための入れ替え回数の偶奇が、zeroDistanceの偶奇と等しければ解ける->終了
        for i in range(1,10):
            if copyStart == goal:
                if cnt % 2 == zeroDistance:     # 条件を満たした場合
                    start[start.index(9)] = 0       # 9を0に戻す
                    print("start:{0}".format(start))
                    return cnvListToInt(start)      # int化したstartを返す
                continue                        # 条件を満たさない場合、ループの最初に戻る
            targetIndex = copyStart.index(i)
            if targetIndex != i-1:          # iの配置が異なれば入れ替える
                copyStart = swap(copyStart, targetIndex, i-1)
                cnt += 1

# 1探索ごとに集計したresultsを各要素ごとに集計する関数
def getTotalData(results: list) -> dict:
    runCnt = len(results)
    puzzleRoutes = []   # 経路リスト
    routeLengths = []   # 経路リストの長さ
    searchTimes = []    # 実行時間
    searchCnts = []     # 処理回数
    for result in results:
        puzzleRoutes.append(result["puzzleRoute"])
        routeLengths.append(result["routeLength"])
        searchTimes.append(result["searchTime"])
        searchCnts.append(result["searchCnt"])
    
    totalData = {"runCnt": runCnt, "puzzleRoutes": puzzleRoutes, "routeLengths": routeLengths,
                 "searchTimes": searchTimes, "searchCnts": searchCnts}
    return totalData

# printとファイル出力用に、集計結果の文字列を返す関数
def getMeanStr(searchType: SearchType, totalData: dict) -> str:
    runCnt = totalData["runCnt"]
    meanRouteLength = sum(totalData["routeLengths"])/runCnt
    meanSearchTimes = sum(totalData["searchTimes"])/runCnt
    meanSearchCnts = sum(totalData["searchCnts"])/runCnt
    
    meanStr = ("探索アルゴリズム：{0:5} | 実行回数：{1}回 | 平均実行時間：{2:9.6f}秒 | " 
               "平均処理回数：{3:8}回 | 平均経路長：{4}").format(
        searchType.value, runCnt, meanSearchTimes, meanSearchCnts, meanRouteLength)
    return meanStr

# 集計結果と経路をテキストファイルに出力する関数
def outputResult(path: str, totalData: dict, meanStr: str, searchType: SearchType) -> None:
    with open(path, mode='w') as f:
        f.write('探索アルゴリズム：{}\n'.format(searchType.name))
        f.write(meanStr + '\n')
        for i in range(totalData["runCnt"]):
            f.write("\n------------------------------------------------\n\n")
            f.write("経路{0} 実行時間：{1:.4f}秒 処理回数：{2}回 経路長：{3}\n"
                    .format(i+1, totalData["searchTimes"][i], totalData["searchCnts"][i],
                            totalData["routeLengths"][i]))
            puzzleRoute = totalData["puzzleRoutes"][i]
            for j in range(len(puzzleRoute)):
                puzzleInt = puzzleRoute[j]
                f.write("{0:>6}: {1:09}\n".format(j+1, puzzleInt))

# main関数。探索アルゴリズム（複数可）・完成形・探索回数・出力先のパスを引数にわたす。
def main(*searchTypes: SearchType, GOAL_INT: int = 123804765, 
         runCnt: int = 10, outputDirectoryPath: str = '8パズル探索結果/'):
    
    start = time.time()
    results = defaultdict(list)     # 探索結果
    for i in range(runCnt):
        print("探索{} ".format(i+1), end="")
        START_INT = makePuzzle(GOAL_INT)    # パズル作成
        if SearchType.ALL in searchTypes:   # SearchType.ALLが指定された場合、
            searchTypes = (SearchType.BFS, SearchType.DFS, SearchType.ASTAR)    # タプルsearchTypesを上書き
        for searchType in searchTypes:      # 指定されたアルゴリズムで実行し、resultsに追加
            results[searchType].append((searchAlgorithm(START_INT, GOAL_INT, searchType)))
    
    # 指定パスのフォルダが存在しない場合は作成
    if not os.path.exists(outputDirectoryPath):
        os.mkdir(outputDirectoryPath)
    
    print("{0}集計結果{1}".format(Color.ACCENT, Color.END))
    
    for searchType, result in results.items():
        totalData = getTotalData(result)        # 集計
        meanStr = getMeanStr(searchType, totalData)     # 集計結果の文字列
        print(meanStr)
        outputFilePath = outputDirectoryPath + searchType.value + '.txt'    # アルゴリズムごとにファイル名を変更
        outputResult(outputFilePath, totalData, meanStr, searchType)    # 集計結果と経路を出力
    
    print("総時間：{:.6f}秒".format(time.time() - start))
    print("{0}All Complete!{1}".format(Color.GREEN, Color.END))

main(SearchType.ALL, GOAL_INT=123456780, runCnt=100)
