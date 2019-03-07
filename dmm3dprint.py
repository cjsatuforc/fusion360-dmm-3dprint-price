#Author-Shungiku
#Description-Estimate the printing fee\t

#rev20180503a

import adsk.core, adsk.fusion, traceback

commandId = 'DMM3DPrintCommand'
commandName = 'DMM3DPrint'
commandDescription = 'Estimate the printing fee'

app = None
ui = None

handlers = []

modelVolume = 0
boundaryVolume = 0
index = 0

app = adsk.core.Application.get()
if app:
    ui = app.userInterface
    
    
def getSelectedEntities(selectionInput):
    entities = []
    for x in range(0, selectionInput.selectionCount):
        mySelection = selectionInput.selection(x)
        selectedObj = mySelection.entity
        if type(selectedObj) is adsk.fusion.BRepBody or type(selectedObj) is adsk.fusion.MeshBody or type(selectedObj) is adsk.fusion.Component:
            entities.append(selectedObj)
        elif type(selectedObj) is adsk.fusion.Occurrence:
            entities.append(selectedObj.component)
    return entities


class DMM3DPrintInputChangedHandler(adsk.core.InputChangedEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        try:
            cmd = args.firingEvent.sender
            inputs = cmd.commandInputs
            global commandId
            
            for inputI in inputs:
                if inputI.id == commandId + '_selection':
                    selectionInput = inputI
                    entities = getSelectedEntities(selectionInput)
                    try:
                        global modelVolume
                        
                        if type(entities[0]) == adsk.fusion.MeshBody:
                            modelVolume = meshVolume(entities[0])
                            global boundaryVolume
                            boundaryVolume = meshBoundary(entities[0])
                            
                        else:
                            modelVolume = round(entities[0].volume, 3)
                            
                            box = entities[0].boundingBox
                            length_cm = box.maxPoint.x - box.minPoint.x
                            width_cm = box.maxPoint.y - box.minPoint.y
                            height_cm = box.maxPoint.z - box.minPoint.z
                        
                            global boundaryVolume
                            boundaryVolume = round(length_cm * width_cm * height_cm, 3)
                    
                    except:
                        modelVolume = 0
                        boundaryVolume = 0
                        
                    inputs.itemById(commandId + '_modelVolume').text = str(modelVolume) + ' cm^3'
                    inputs.itemById(commandId + '_boundaryVolume').text = str(boundaryVolume) + ' cm^3'
                    global index
                    inputs.itemById(commandId + '_price').text = dmmPrice()
                    
                    
                        
                elif inputI.id == commandId + '_dmmMaterial':
                    dmmMaterialInput = inputI
                    index = dmmMaterialInput.selectedItem.index
                    inputs.itemById(commandId + '_price').text = dmmPrice()

        except:
            if ui:
                ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
         
         
class DMM3DPrintCommandCreatedHandler(adsk.core.CommandCreatedEventHandler):    
    def __init__(self):
        super().__init__()        
    def notify(self, args):
        try:
            cmd = args.command
            cmd.isRepeatable = False
            onExecute = DMM3DPrintCommandExecuteHandler()
            cmd.execute.add(onExecute)
            onDestroy = DMM3DPrintCommandDestroyHandler()
            cmd.destroy.add(onDestroy)
            onInputChanged = DMM3DPrintInputChangedHandler()
            cmd.inputChanged.add(onInputChanged)
            # keep the handler referenced beyond this function
            handlers.append(onExecute)
            handlers.append(onDestroy)
            handlers.append(onInputChanged)

            # Define the inputs.
            inputs = cmd.commandInputs
            
            global commandId
            
            selectionInput = inputs.addSelectionInput(commandId + '_selection', '選択', 'Select bodies')
            selectionInput.setSelectionLimits(0, 1)
            selectionInput.selectionFilters = ['SolidBodies', 'MeshBodies']
            # selectionInput.selectionFilters = ['SolidBodies', 'MeshBodies', 'Occurrences']
            
            global modelVolume
            modelVolumeInput = inputs.addTextBoxCommandInput(commandId + '_modelVolume', 'モデル', str(modelVolume) + ' cm^3', 1, True)
            global boundaryVolume
            boundaryVolumeInput = inputs.addTextBoxCommandInput(commandId + '_boundaryVolume', 'バウンディングボックス', str(boundaryVolume) + ' cm^3', 1, True)
            global index
            dmmMaterialInput = inputs.addDropDownCommandInput(commandId + '_dmmMaterial', '素材', adsk.core.DropDownStyles.LabeledIconDropDownStyle)
            listItems = dmmMaterialInput.listItems
            for dmmMaterialName in dmmMaterialPrice :
                listItems.add(dmmMaterialName[0], False)
            listItems[8].isSelected = True
            
            groupCmdInput = inputs.addGroupCommandInput(commandId + 'group2', '見積金額')
            groupCmdInput.isExpanded = True
            groupCmdInput.isEnabledCheckBoxDisplayed = False
            groupChildInputs = groupCmdInput.children
            
            
            price = dmmPrice()
            priceInput = groupChildInputs.addTextBoxCommandInput(commandId + '_price', '造形費', price, 1, True)
            groupChildInputs.addTextBoxCommandInput(commandId + '_shipping', '送料', '無料', 1, True)
            message = '<div align="center">Go to <a href="https://make.dmm.com/print/">DMM 3D Print</a></div>'
            groupChildInputs.addTextBoxCommandInput(commandId + '_url', '', message, 1, True)
            
        except:
            if ui:
                ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
                
    
class DMM3DPrintCommandExecuteHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        try:
            adsk.terminate()
        except:
            if ui:
                ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

class DMM3DPrintCommandDestroyHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        try:
            # when the command is done, terminate the script
            # this will release all globals which will remove all event handlers
            adsk.terminate()
        except:
            if ui:
                ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


def dmmPrice():
    global modelVolume
    global boundaryVolume
    global index
    price = (modelVolume * dmmMaterialPrice[index][1] + boundaryVolume * dmmMaterialPrice[index][2] + dmmMaterialPrice[index][3])*1.08
    if price == 0 :
        price = '問い合わせ'
    else :
        price = str(int(price))+ ' 円'
    return str(price)


def signedVolumeOfTriangle(p1, p2, p3):
    v321 = p3[0]*p2[1]*p1[2]
    v231 = p2[0]*p3[1]*p1[2]
    v312 = p3[0]*p1[1]*p2[2]
    v132 = p1[0]*p3[1]*p2[2]
    v213 = p2[0]*p1[1]*p3[2]
    v123 = p1[0]*p2[1]*p3[2]
    return (1.0/6.0)*(-v321 + v231 + v312 - v132 - v213 + v123)



def meshVolume(body):
    # 三角メッシュのみ
    mesh = body.displayMesh
    nodeCoordinatesAsFloat = mesh.nodeCoordinatesAsFloat
    nodeIndices = mesh.nodeIndices
    
    # ノードごとのXYZ座標を割り当て
    n = [nodeCoordinatesAsFloat[i:i+3] for i in range(0, len(nodeCoordinatesAsFloat), 3)]
    #print(n)
    
    # 面に対応するノードを割り当て
    ni = [nodeIndices[i:i+3] for i in range(0, len(nodeIndices), 3)]
    #print(ni)
    
    # 面ごとにリストを分割
    p = []
    for i in range(len(ni)):
        p.append([n[ni[i][0]], n[ni[i][1]], n[ni[i][2]]])
    #print(p)
        
    totalVolume = 0
    for i in p:
        totalVolume += signedVolumeOfTriangle(i[0], i[1], i[2])
    #print(str(totalVolume)+' cm^3')
    return round(totalVolume, 3)


def meshBoundary(body):
    mesh = body.displayMesh
    nodeCoordinatesAsFloat = mesh.nodeCoordinatesAsFloat
    x = nodeCoordinatesAsFloat[::3]
    y = nodeCoordinatesAsFloat[1::3]
    z = nodeCoordinatesAsFloat[2::3]
    
    xMax = max(x)
    xMin = min(x)
    yMax = max(y)
    yMin = min(y)
    zMax = max(z)
    zMin = min(z)
    length_cm = xMax - xMin
    width_cm = yMax - yMin
    height_cm = zMax - zMin
    
    boundaryVolume = round(length_cm * width_cm * height_cm, 3)
    
    return boundaryVolume
    
    
def run(context):
    try:
        cmdDef = ui.commandDefinitions.itemById(commandId)
        if not cmdDef:
            cmdDef = ui.commandDefinitions.addButtonDefinition(commandId, commandName, commandDescription) # no resource folder is specified, the default one will be used

        onCommandCreated = DMM3DPrintCommandCreatedHandler()
        cmdDef.commandCreated.add(onCommandCreated)
        # keep the handler referenced beyond this function
        handlers.append(onCommandCreated)

        inputs = adsk.core.NamedValues.create()
        cmdDef.execute(inputs)

        # prevent this module from being terminate when the script returns, because we are waiting for event handlers to fire
        adsk.autoTerminate(False)

    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
            

dmmMaterialPrice = [
    ["石膏", 126, 10.5, 420],
    ["フルカラープラスチック", 250, 10, 1799],
    ["ガラス", 0, 150, 21000],
    ["アクリル (UltraMode) 半透明", 250, 10, 1799],
    ["アクリル (UltraMode) カラー", 250, 10, 1899],
    ["アクリル (XtremeMode)", 500, 25, 1799],
    ["クリアアクリル", 157.5, 19.95, 1260],
    ["ポリカーボネート／PC-ABS", 84, 84, 1680],
    ["ナイロン ホワイト", 17.85, 8.4, 420],
    ["ナイロン カラー", 17.85, 8.4, 1050],
    ["ナイロン ホワイト磨き", 17.85, 8.4, 735],
    ["ナイロン カラー磨き", 17.85, 8.4, 1365],
    ["ガラスビーズ強化ナイロン", 52.5, 210, 31500],
    ["ABSライク", 170.1, 31.5, 1260],
    ["ゴムライク FLX9995", 157.5, 19.95, 1260],
    ["ゴムライク FLX9985", 157.5, 19.95, 1365],
    ["ゴムライク FLX9970", 157.5, 19.95, 1470],
    ["ゴムライク FLX9960", 157.5, 19.95, 1575],
    ["ゴムライク FLX9950", 157.5, 19.95, 1680],
    ["ゴムライク FLX9940", 157.5, 19.95, 1785],
    ["ゴムライク Tango+", 157.5, 19.95, 1890],
    ["ゴムライク RGD8630", 157.5, 19.95, 1260],
    ["アルミ 未処理", 1875, 0, 60000],
    ["アルミ ショットブラスト研磨処理", 1875, 0, 66000],
    ["アルミ 硬質アルマイト処理", 1875, 0, 69750],
    ["アルミ テフロン加工", 1875, 0, 72000],
    ["チタン", 1050, 84, 2100],
    ["チタン 磨き", 1050, 84, 4200],
    ["真鍮 未処理", 3000, 150, 2250],
    ["真鍮 鏡面", 3000, 150, 3300],
    ["真鍮 K24メッキ", 3000, 150, 5100],
    ["真鍮 K18メッキ", 3000, 150, 4950],
    ["真鍮 K14メッキ", 3000, 150, 4800],
    ["真鍮 ピンクゴールドメッキ", 3000, 150, 4650],
    ["真鍮 ロジウムメッキ", 3000, 150, 4500],
    ["真鍮 ブラックロジウムメッキ", 3000, 150, 4500],
    ["真鍮 ガンメタロジウムメッキ", 3000, 150, 4500],
    ["シルバー 未処理", 3750, 150, 2250],
    ["シルバー バレル研磨", 3750, 150, 2700],
    ["シルバー 鏡面", 3750, 150, 3300],
    ["シルバー いぶし仕上げ", 3750, 150, 4800],
    ["シルバー 梨地仕上げ", 3750, 150, 4800],
    ["シルバー ヘアライン", 3750, 150, 4800],
    ["ゴールド", 0, 0, 0],
    ["プラチナ", 0, 0, 0],
    ["マルエージング鋼", 3375, 187.5, 31250],
    ["インコネル", 2688, 187.5, 75000],
    ["ジュラルミン", 1500, 150, 3000],
    ["ステンレス SUS304", 1800, 150, 3000],
    ["ベリリウム鋼", 2100, 150, 3000],
    ["スチール ナチュラル", 800, 50, 1890],
    ["スチール ゴールド", 800, 50, 2499],
    ["スチール ブラック", 800, 50, 2499],
    ["スチール ブラウン", 800, 50, 1899],
    ["PPS", 0, 0, 0],
    ["光造形樹脂", 200, 0, 1800],
    ["カーボン複合素材", 0, 0, 0],
    ["64チタン", 1250, 100, 3800],
    ["ステンレス SUS316L", 100, 1900, 2500],
    ["MJF ナチュラル", 52.5, 6.3, 420],
    ["MJF ブラック", 52.5, 6.3, 1050],
    ["MJF ブラック磨き", 52.5, 6.3, 1365],
    ["MJF グラファイト", 52.5, 6.3, 788]
]
