def inputOptionsValid(options, amc_major_fw_ver):
    """
    Sanity check on input options

    options - an optparser.Values instance
    amc_major_fw_ver - major FW version of the AMC
    """

    # get the options dictionary
    dict_options = options.__dict__.keys()

    # Cal Phase
    if "CalPhase" in dict_options:
        if amc_major_fw_ver < 3:
            if options.CalPhase < 0 or options.CalPhase > 8:
                print 'CalPhase must be in the range 0-8'
                return False
            pass
        else:
            if options.CalPhase < 0 or options.CalPhase > 7:
                print 'CalPhase must be in the range 0-7'
                return False
            pass
        pass
    
    # CFG_CAL_SF
    if "calSF" in dict_options and amc_major_fw_ver >= 3: # V3 Behavior only
        if options.calSF < 0 or options.calSF > 3:
            print 'calSF must be in the range 0-3'
            return False
        pass
    
    # Channel Range
    if (("chMin" in dict_options) and ("chMax" in dict_options)):
        if not (0 <= options.chMin <= options.chMax < 128):
            print "chMin %d not in [0,%d] or chMax %d not in [%d,127] or chMax < chMin"%(options.chMin,options.chMax,options.chMax,options.chMin)
            return False
        pass

    # MSPL or Pulse Stretch
    if "MSPL" in dict_options:
        if amc_major_fw_ver < 3:
            if options.MSPL not in range(1,9):
                print("Invalid MSPL specified: %d, must be in range [1,8]"%(options.MSPL))
                return False
            pass
        else:
            if options.MSPL not in range(0,8):
                print("Invalid MSPL specified: %d, must be in range [1,8]"%(options.MSPL))
                return False
            pass
        pass

    # step size
    if "stepSize" in dict_options:
        if options.stepSize <= 0:
            print("Invalid stepSize specified: %d, must be in range [1, %d]"%(options.stepSize, options.scanmax-options.scanmin))
            return False
        pass

    # VThreshold2
    if ( ("vt2" in dict_options) and (amc_major_fw_ver < 3)): # Only v2b behavior
        if options.vt2 not in range(256):
            print("Invalid VT2 specified: %d, must be in range [0,255]"%(options.vt2))
            return False
        pass

    return True

def launchSCurve(**kwargs):
    """
    Launches an scurve scan at a given set of trim settings

    Support arguments:
    calSF - int, value of the CFG_CAL_FS register
    cardName - string, name or ip address of AMC in uTCA crate
    chMask - array of ints, size 3072, indicates channels to mask; idx = vfatN * 128 + channel
    chMax - int, maximum channel
    chMin - int, minimum channel
    debug - boolean, print debugging information
    filename - string, physical filename indicating absolute path of scurve outputfile
    latency - int, latency to take the scruve at
    link - int, optohybrid number on cardName
    mspl - int, value of MSPL or CFG_PULSE_STRETCH to use
    nevts - int, number of events to take in the scan
    setChanRegs - boolean, write VFAT channel registers if True
    vfatmask - int, vfatmask to use apply, 24-bit number, 1 in n^th bit indicates n^th vfat is masked
    voltageStepPulse - boolean, use voltage step pulse (true) instead of current pulse (false)
    trimARM - array of ints, size 3072, indicating trim amplitude to set for arming comparator; idx = vfatN * 128 + channel
    trimARMPol - as trimARM but sets trim polarity
    trimZCC - as trimARM but for the ZCC comparator
    trimZCCPol - as trimZCC but sets trim polarity
    """


    # Set defaults
    calSF = 0
    cardName = None
    chMask = None
    chMax = 127
    chMin = 0
    debug = False
    filename = None
    latency = 33
    link = 0
    mspl = 3
    nevts = 100
    setChanRegs = False
    vfatmask = 0x0
    voltageStepPulse = False
    trimARM = None
    trimARMPol = None
    trimZCC = None
    trimZCCPol = None

    # Get defaults from kwargs
    if "calSF" in kwargs:
        calSF = kwargs["calSF"]
    if "cardName" in kwargs:
        cardName = kwargs["cardName"]
    if "chMask" in kwargs:
        chMask = kwargs["chMask"]
    if "chMax" in kwargs:
        chMax = kwargs["chMax"]
    if "chMin" in kwargs:
        chMin = kwargs["chMin"]
    if "debug" in kwargs:
        debug = kwargs["debug"]
    if "filename" in kwargs:
        filename = kwargs["filename"]
    if "latency" in kwargs:
        latency = kwargs["latency"]
    if "link" in kwargs:
        link = kwargs["link"]
    if "mspl" in kwargs:
        mspl = kwargs["mspl"]
    if "nevts" in kwargs:
        nevts = kwargs["nevts"]
    if "setChanRegs" in kwargs:
        setChanRegs = kwargs["setChanRegs"]
    if "vfatmask" in kwargs:
        vfatmask = kwargs["vfatmask"]
    if "voltageStepPulse" in kwargs:
        voltageStepPulse = kwargs["voltageStepPulse"]
    if "trimARM" in kwargs:
        trimARM = kwargs["trimARM"]
    if "trimARMPol" in kwargs:
        trimARMPol = kwargs["trimARMPol"]
    if "trimZCC" in kwargs:
        trimZCC = kwargs["trimZCC"]
    if "trimZCCPol" in kwargs:
        trimZCCPol = kwargs["trimZCCPol"]

    # Check minimum arguments
    import os
    if cardName is None:
        print("launchSCurve(): You must provide either an AMC network alias (e.g. "eagle60") or an AMC ip address. Exiting")
        exit(os.EX_USAGE)
    if filename is None:
        print("launchSCurve(): You must provide a filename for this scurve. Exiting")
        exit(os.EX_USAGE)

    # Set the channel registers
    from gempython.tools.vfat_user_functions_xhal import *
    if setChanRegs:
        if debug:
            print("opening an RPC connection to %s"%cardName)
        vfatBoard = HwVFAT(cardName, link, debug)

        if debug:
            print("setting channel registers")
        rpcResp = vfatBoard.setAllChannelRegisters(chMask=chMask, trimARM=trimARM, trimARMPol=trimARMPol, trimZCC=trimZCC, trimZCCPol=trimZCCPol, vfatMask=vfatmask, debug=debug)

        if rpcResp != 0:
            raise Exception("RPC response was non-zero, setting channel registers failed")

    # Make the command to be launched
    cmd = [ "ultraScurve.py",
            "--cardName=%s"%(cardName),
            "-g%d"%(link),
            "--chMin=%i"%(chMin),
            "--chMax=%i"%(chMax),
            "--latency=%i"%(latency),
            "--mspl=%i"%(mspl),
            "--nevts=%i"%(nevts),
            "--vfatmask=0x%x"%(vfatmask),
            "--filename=%s"%(filename)
            ]
    if voltageStepPulse:
        cmd.append("--voltageStepPulse")
    else:
        cmd.append("--calSF=%i"%(calSF) )

    # launch the command
    from gempython.utils.wrappers import runCommand
    if debug:
        print("launching an scurve with command:")
        command = ""
        for word in cmd:
            command = "%s %s"%(command, word)
        print(command)
    print("launching scurve for filename: %s"%filename)
    runCommand(cmd)
    
    return

def readBackCheck(rootTree, dict_Names, device, gtx, vt1bump=0):
    """
    Given an input set of registers, and expected values of those registers, read from all VFATs on device.gtx to see if there are any differences between written and read values.

    rootTree - name of a TTree that has values that should have been written
    dict_Names - dictionary where key names are the branch names in rootTree and the values are the register names they correspond too
    device - optohybrid the vfats belong to that you want to check
    gtx - link of this optohybrid
    """

    from gempython.tools.vfat_user_functions_uhal import *
    
    import numpy as np
    import root_numpy as rp
    import ROOT as r
    import sys
    
    # Check that the requested register is supported
    list_KnownRegs = parameters.defaultValues.keys()
    list_KnownRegs.append("VThreshold1")
    list_KnownRegs.append("VFATChannels.ChanReg")
    list_KnownRegs.append("ChipID")
    for regName in dict_Names.values():
        if regName not in list_KnownRegs:
            print "readBackCheck() does not understand %s"%(regName)
            print "readBackCheck() is only supported for registers:", list_KnownRegs
            sys.exit(-1)

    # Get data from tree
    list_bNames = dict_Names.keys()
    list_bNames.append('vfatN')
    #list_bNames.append('vfatID')
    if "trimDAC" in dict_Names.keys() or "mask" in dict_Names.keys():
        list_bNames.append('vfatCH')
    array_writeVals = rp.tree2array(tree=rootTree, branches=list_bNames)

    # Get data from VFATs
    perreg   = "0x%02x"
    for bName,regName in dict_Names.iteritems():
        print "Reading back (%s,%s) from all VFATs, any potential mismatches will be reported below"%(bName,regName)
        print "="*40
        
        regMap = []
        regValues = []
        if regName == "VFATChannels.ChanReg": #Channel Register, use 0x1f
            for chan in range(0,128):
                regValues = readAllVFATs(device, gtx, regName+"%d"%(chan), 0x0)
                #regMap = map(lambda chip: chip&0x1f, regValues)
                
                for vfat,readBackVal in enumerate(regValues):
                    writeValsPerVFAT = array_writeVals[ array_writeVals['vfatN'] == vfat]
                    writeValsPerVFAT = writeValsPerVFAT[ writeValsPerVFAT['vfatCH'] == chan]
                    writeValOfReg = np.asscalar(writeValsPerVFAT['%s'%bName]) 
                    if bName == "mask":
                        if writeValOfReg != ((readBackVal&0x20)%31): #trimDAC goes from 0 -> 31, leftover is mask
                            print "VFAT%i Chan%i: %s mismatch, write val = %i, readback = %i"%(vfat, chan, bName, writeValOfReg, (readBackVal&0x20)%31)
                    else:
                        if writeValOfReg != (readBackVal&0x1f):
                            print "VFAT%i Chan%i: %s mismatch, write val = %i, readback = %i"%(vfat, chan, bName, writeValOfReg, readBackVal&0x1f)
        elif regName == "ChipID": #ChipID
            regValues = getAllChipIDs(device, gtx, 0x0) # dict of { vfatN:chipID }
            for vfat in regValues:
                valsPerVFAT = array_writeVals[ array_writeVals['vfatN'] == vfat]
                valOfReg = np.asscalar(np.unique(valsPerVFAT['%s'%bName]))
                if valOfReg != regValues[vfat]:
                    print "VFAT%i: %s mismatch, expected = %s, readback = %s"%(vfat, regName, hex(valOfReg), hex(regValues[vfat]))
        else: #VFAT Register, use 0xff
            regValues = readAllVFATs(device, gtx, regName, 0x0)
            regMap = map(lambda chip: chip&0xff, regValues)

            for vfat,readBackVal in enumerate(regMap):
                writeValsPerVFAT = array_writeVals[ array_writeVals['vfatN'] == vfat]
                writeValOfReg = np.asscalar(writeValsPerVFAT['%s'%bName])
                if regName == "VThreshold1":
                    writeValOfReg+=vt1bump
                if writeValOfReg != readBackVal:
                    print "VFAT%i: %s mismatch, write val = %i, readback = %i"%(vfat, regName, writeValOfReg, readBackVal)

    return

def setChannelRegisters(vfatBoard, chTree, mask, debug=False):
    """
    vfatBoard - an instance of the HwVFAT class
    chTree - TTree generated from a chConfig.txt file
    mask - vfat mask to apply
    debug - print additional information if True
    """

    from ctypes import *
    
    # Make the cArrays
    cArray_Masks = (c_uint32 * 3072)()
    cArray_trimVal = (c_uint32 * 3072)()
    cArray_trimPol = (c_uint32 * 3072)()

    for event in chTree :
        # Skip masked vfats
        if (mask >> int(event.vfatN)) & 0x1:
            continue

        if (vfatBoard.parentOH.parentAMC.fwVersion > 2):
            cArray_Masks[128*event.vfatN+event.vfatCH] = event.mask
            cArray_trimVal[128*event.vfatN+event.vfatCH] = event.trimDAC
            cArray_trimPol[128*event.vfatN+event.vfatCH] = event.trimPolarity
        else:
            if int(event.vfatCH) == 0:
                vfatBoard.writeVFAT(ohboard, options.gtx, int(event.vfatN), "ContReg3", int(event.trimRange),options.debug)
            if event.mask==0 and event.trimDAC==0:
                continue
            vfatBoard.setChannelRegister(chip=int(event.vfatN), chan=int(event.vfatCH), mask=int(event.mask), trimARM=int(event.trimDAC), debug=options.debug)
            pass
        pass
    
    if (vfatBoard.parentOH.parentAMC.fwVersion > 2):
        rpcResp = vfatBoard.setAllChannelRegisters(
                chMask=cArray_Masks,
                trimARM=cArray_trimVal,
                trimARMPol=cArray_trimPol,
                vfatMask=mask,
                debug=debug)

        if rpcResp != 0:
            raise Exception("RPC response was non-zero, setting trim values for all channels failed")
        pass
    return
