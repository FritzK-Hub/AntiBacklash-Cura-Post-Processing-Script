# This script is based on "Backlash Compensation: Test and gcode Compensation Program" 
# by steaksndwich on Thingiverse
#
# https://www.thingiverse.com/steaksndwich/designs
# https://www.thingiverse.com/thing:3060573
#
# This script is free software. It comes without any warranty
# Antibacklash can help you to compensate Backlash issues if there is no way to resolve it on the Hardware
# (e.g. tighten Belts, Pulleys, Steppermount etc.)
# Antibacklash is meant to be used for cartesian FDM Printers.
# Only use it with Absolute Positioning (G90 must be in start gcode)


from ..Script import Script
from UM.Logger import Logger
from UM.Message import Message
from UM.i18n import i18nCatalog
from dataclasses import dataclass
import re
import math
import copy

@dataclass
class soffset:
    val: float
    change: bool

@dataclass
class soffsets:
    x: soffset
    y: soffset

@dataclass
class sline:
    read: str
    write: str
    dummy: str
    G: int
    F: int
    X: float
    Y: float
    Z: float
    E: float
    nX: float
    nY: float
    seenF: bool
    seenX: bool
    seenY: bool
    seenZ: bool
    seenE: bool
    isErrorPossible: bool
    isG91Active: bool
    readOK: bool
    blX: bool
    blY: bool
    blXchange: bool
    blYchange: bool
    G90: bool
    isMove: bool

@dataclass
class scoord:
    x: float
    y: float
    blX: bool
    blY: bool


class AntibacklashCura(Script):
    def __init__(self):
        super().__init__()

    def getSettingDataString(self):
        return """{
            "name": "AntibacklashCura",
            "key": "AntibacklashCura",
            "metadata": {},
            "version": 2,
            "settings":
            {
                "info_message":
                {
                    "label": "Hover for Information",
                    "description": "This script is free software. It comes without any warranty\\nAntibacklash can help you to compensate Backlash issues if there is no way to resolve it on the Hardware\\n(e.g. tighten Belts, Pulleys, Steppermount etc.)\\nAntibacklash is meant to be used for cartesian FDM Printers.\\nOnly use it with Absolute Positioning (G90 must be in start gcode)\\nAlways check the generated .gcode for errors before starting a print and don't leave the printer unattended. Only continue to use Antibacklash if you know what you are doing!", 
                    "type": "bool",
                    "default_value": false
                },  
                "backlash_speed":
                {
                    "label": "Backlash Speed",
                    "description": "The speed of the extruder on backlash travel moves.",
                    "unit": "mm/min",
                    "type": "float",
                    "default_value": 9000.0
                },
                "backlash_delta":
                {
                    "label": "Backlash Delta",
                    "description": "Increases the tolerance for the backlash detection. If your sliced model has shifted layer lines increase this value. Start with a small value like 0.5 and go up/down from there.",
                    "unit": "μm",
                    "type": "float",
                    "default_value": 0.0
                },
                "x_backlash":
                {
                    "label": "X Backlash",
                    "description": "The amount of backlash compensation for the X axis.",
                    "unit": "mm",
                    "type": "float",
                    "default_value": 0.0
                },
                "y_backlash":
                {
                    "label": "Y Backlash",
                    "description": "The amount of backlash compensation for the Y axis.",
                    "unit": "mm",
                    "type": "float",
                    "default_value": 0.0
                },
                "z_offset":
                {
                    "label": "Z Offset",
                    "description": "The amount of offset for Z-Axis moves. Not from the original Antibacklash program. It's a fix for my printer, but maybe you can benefit from it as well.",
                    "unit": "mm",
                    "type": "float",
                    "default_value": 0.0
                },
                "z_line_number":
                {
                    "label": "Z Offset Layers", 
                    "description": "How many layers are adjusted. From the bottom up.",
                    "type": "int",
                    "default_value": 0
                }
            }
        }"""


    def addbacklash(self, line, offset, coord, delta) -> sline:
        if line.seenX and offset.x.change:
            if coord.blX:
                if line.X + offset.x.val >= coord.x - delta:
                    line.nX = line.X + offset.x.val
                    line.blX = True
                elif (line.X + offset.x.val) < coord.x + delta:
                    line.nX = line.X
                    line.blX = False
                    line.blXchange = True
            else:
                if line.X > coord.x - delta:
                    line.nX = line.X + offset.x.val
                    line.blX = True
                    line.blXchange = True
                elif line.X <= coord.x + delta:
                    line.nX = line.X
                    line.blX = False
        elif line.seenX:
            line.nX = line.X
        
        if line.seenY and offset.y.change:
            if coord.blY:
                if line.Y + offset.y.val >= coord.y - delta:
                    line.nY = line.Y + offset.y.val
                    line.blY = True
                elif (line.Y + offset.y.val) < coord.y + delta:
                    line.nY = line.Y
                    line.blY = False
                    line.blYchange = True
            else:
                if line.Y > coord.y - delta:
                    line.nY = line.Y + offset.y.val
                    line.blY = True
                    line.blYchange = True
                elif line.Y <= coord.y + delta:
                    line.nY = line.Y
                    line.blY = False
        elif line.seenY:
            line.nY = line.Y
 
    
    def applyTravel(self, line, offset, coord, speed) -> sline:
        nline: sline = copy.deepcopy(line)
        if offset.x.change:
            if nline.blXchange:
                if coord.blX:
                    nline.nX = coord.x - offset.x.val
                else:
                    nline.nX = coord.x + offset.x.val
            else:
                nline.nX = coord.x
        else:
            nline.nX = coord.x

        if offset.y.change:
            if nline.blYchange:
                if coord.blY:
                    nline.nY = coord.y - offset.y.val
                else:
                    nline.nY = coord.y + offset.y.val
            else:
                nline.nY = coord.y
        else:
            nline.nY = coord.y
        
        nline.write = f"G{nline.G} "
        if nline.seenF:
            nline.write += f"F{speed} "
        if nline.seenX:
            nline.write += f"X{round(nline.nX, 3)} "
        if nline.seenY:
            nline.write += f"Y{round(nline.nY, 3)} "
        nline.write += ";                            Backlash compensated"        

        return nline

    def getNewLine(self, gline, G91) -> sline:
        line = self.plainLine()
        line.read = gline
        line.isG91Active = G91
        gline = gline.split(' ')
        if gline[0].startswith("G90"):
            line.G90 = True
        if line.isG91Active and line.G90:
            line.isG91Active = False
        else:
            if gline[0].startswith("G91"):
                line.isG91Active = True
            elif gline[0].startswith("G0") or gline[0].startswith("G1"):
                line.isMove = True
                line.G = int(gline[0][1])
                for field in enumerate(gline[1:]):
                    value = round(float(field[1][1:]), 5)
                    if field[1].startswith("F"):
                        line.seenF = True
                        line.F = round(value)
                        continue
                    if field[1].startswith("X"):
                        line.seenX = True
                        line.X = value
                        continue
                    if field[1].startswith("Y"):
                        line.seenY = True
                        line.Y = value
                        continue
                    if field[1].startswith("Z"):
                        line.seenZ = True
                        line.Z += value
                        continue
                    if field[1].startswith("E"):
                        line.seenE = True
                        line.E = value
                        continue
        return line

    def generateLine(self, line: sline, F) -> sline:
        line.write = f"G{line.G} "
        if F > 0:
            line.write += f"F{F} "
        if line.seenX:
            line.write += f"X{round(line.nX, 3)} "
        if line.seenY:
            line.write += f"Y{round(line.nY, 3)} "
        if line.seenZ:
            line.write += f"Z{round(line.Z, 3)} "
        if line.seenE:
            line.write += f"E{round(line.E, 3)} "
 
    def readToWrite(self, line: sline) -> sline:
        if not line.isMove:
            line.write = line.read
            return
        line.write = f"G{line.G} "
        if line.seenF:
            line.write += f"F{line.F} "
        if line.seenX:
            line.write += f"X{round(line.X, 3)} "
        if line.seenY:
            line.write += f"Y{round(line.Y, 3)} "
        if line.seenZ:
            line.write += f"Z{round(line.Z, 3)} "
        if line.seenE:
            line.write += f"E{round(line.E, 3)} "   

    def plainLine(self) -> sline:
        line = sline("","","",0,0,0.0,0.0,0.0,0.0,0.0,0.0,False,False,False,False,False,False,False,False,False,False,False,False,False,False)
        return line

    def execute(self, data):
        originalData = copy.deepcopy(data)
        catalog = i18nCatalog("cura")
        backlashCompensatedMessage = Message(
            catalog.i18nc("@info:message", "Please validate the file and its Start-/End-Codes. To preview you can use any gcode viewer (e.g. gcode.ws). Use at you own risk! Never leave your printer unattended."),
            title=catalog.i18nc("@info:title", "Conversion Finished [Antibacklash]"),
            message_type=Message.MessageType.POSITIVE
        )
        backlashFailedMessage = Message(
            catalog.i18nc("@info:message", "G90 not found. Please make sure you operate with Absolute Positioning (G90 must be in start gcode)"),
            title=catalog.i18nc("@info:title", "Nothing Changed [Antibacklash]"),
            message_type=Message.MessageType.WARNING
        )

        Logger.log("d", "Available Message Types:")
        for message_type in dir(Message.MessageType):
            Logger.log("d", f"{message_type}")


        seenG90 = False
        xOffset = soffset(self.getSettingValueByKey("x_backlash"), True)
        yOffset = soffset(self.getSettingValueByKey("y_backlash"), True)
        zOffset = self.getSettingValueByKey("z_offset")
        zOffsetCount = self.getSettingValueByKey("z_line_number")
        offset = soffsets(xOffset, yOffset)
        backlashSpeed = self.getSettingValueByKey("backlash_speed")
        backlashDelta = self.getSettingValueByKey("backlash_delta") / 1000.0
        coord = scoord(0.0, 0.0, False, False)
        line: sline = None
        blChange: sline = None
        linecount: int = 0
        lastF = 0.0
        addZ = 0.0


        for layer_number, glayer in enumerate(data):
            glines = glayer.split("\n")
            newlines = []
            if layer_number < zOffsetCount:
                addZ += zOffset
            for line_number, gline in enumerate(glines):
                line = self.getNewLine(gline, False)
                line.Z += addZ
                self.readToWrite(line)
                if line.G90 and (not seenG90):
                    seenG90 = True
                if not seenG90:
                    newlines.append(line.write)
                else:
                    if line.isG91Active:
                        newlines.append(line.write)
                    elif (not line.seenX) and (not line.seenY):
                            newlines.append(line.write)
                    else:
                        self.addbacklash(line, offset, coord, backlashDelta)
                        if ((line.blXchange or line.blYchange) and line.seenE):
                            blChange = self.applyTravel(line, offset, coord, backlashSpeed)
                            newlines.append(blChange.write)
                        self.generateLine(line, lastF)
                        newlines.append(line.write)
                        coord.x = line.nX
                        coord.y = line.nY
                        coord.blX = line.blX
                        coord.blY = line.blY
                if line.seenF:
                    lastF = line.F
            data[layer_number] = "\n".join(newlines)
        
        if seenG90:
            backlashCompensatedMessage.show()
            return data
        else:
            backlashFailedMessage.show()
            return originalData