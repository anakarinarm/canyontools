
## Functions to calculate metrics and write them down

from netCDF4 import Dataset

import numpy as np

import pylab as pl

import scipy.io

import scipy as spy

import xarray as xr

import canyon_tools.readout_tools as rout 
 

#---------------------------------------------------------------------------------------------------------------------------
def getDatasets(expPath, runName):
  '''Specify the experiment and run from which to analyse state and ptracers output.
   expName : (string) Path to experiment folder. E.g. '/ocean/kramosmu/MITgcm/TracerExperiments/BARKLEY', etc.
   runName : (string) Folder name of the run. E.g. 'run01', 'run10', etc
  '''
  Grid = "%s/%s/gridGlob.nc" %(expPath,runName)
  GridOut = Dataset(Grid)

  State =  "%s/%s/stateGlob.nc" %(expPath,runName)
  StateOut = Dataset(State)

  Ptracers =  "%s/%s/ptracersGlob.nc" %(expPath,runName)
  PtracersOut = Dataset(Ptracers)
    
  return (Grid, GridOut, State,StateOut,Ptracers, PtracersOut)


#---------------------------------------------------------------------------------------------------------------------------


def getProfile(Tr,yi,xi,nz0=0,nzf=90):
  '''Slice tracer profile at x,y = xi,yi form depth index k=nz0 to k=nzf. Default values are nz0=0 (surface)
  and nzf = 89, bottom. Tr is a time slice (3D) of the tracer field'''
  IniProf = Tr[nz0:nzf,yi,xi]
  return IniProf


#---------------------------------------------------------------------------------------------------------------------------


def maskExpand(mask,Tr):
  '''Expand the dimensions of mask to fit those of Tr. mask should have one dimension less than Tr (time axis). 
  It adds a dimension before the first one.'''
    
  mask_expand = np.expand_dims(mask,0)
    
  mask_expand = mask_expand + np.zeros(Tr.shape)
    
  return mask_expand

    
#---------------------------------------------------------------------------------------------------------------------------


def howMuchWaterX(Tr,MaskC,nzlim,rA,hFacC,drF,yin,zfin,xi,yi):
  '''
  INPUT----------------------------------------------------------------------------------------------------------------
    Tr    : Array with concentration values for a tracer. Until this function is more general, this should be size 19x90x360x360
    MaskC : Land mask for tracer
    nzlim : The nz index under which to look for water properties
    rA    : Area of cell faces at C points (360x360)
    fFacC : Fraction of open cell (90x360x360)
    drF   : Distance between cell faces (90)
    yin   : across-shore index of shelf break
    zfin  : shelf break index + 1 
    xi    : initial profile x index
    yi    : initial profile y index
    
    OUTPUT----------------------------------------------------------------------------------------------------------------
    VolWaterHighConc =  Array with the volume of water over the shelf [:,:30,227:,:] at every time output.
    Total_Tracer =  Array with the mass of tracer (m^3*[C]*l/m^3) at each x-position over the shelf [:,:30,227:,:] at 
                    every time output. Total mass of tracer at xx on the shelf.
                                                
  -----------------------------------------------------------------------------------------------------------------------
  '''
  
  maskExp = maskExpand(MaskC,Tr)

  TrMask=np.ma.array(Tr,mask=maskExp)   
    
  trlim = TrMask[0,nzlim,yi,xi]
    
  print('tracer limit concentration is: ',trlim)
    
  WaterX = 0
    
  # mask cells with tracer concentration < trlim on shelf
  HighConc_Masked = np.ma.masked_less(TrMask[:,:zfin,yin:,:], trlim) 
  HighConc_Mask = HighConc_Masked.mask
    
  #Get volume of water of cells with relatively high concentration
  rA_exp = np.expand_dims(rA[yin:,:],0)
  drF_exp = np.expand_dims(np.expand_dims(drF[:zfin],1),1)
  rA_exp = rA_exp + np.zeros(hFacC[:zfin,yin:,:].shape)
  drF_exp = drF_exp + np.zeros(hFacC[:zfin,yin:,:].shape)
    
  ShelfVolume = hFacC[:zfin,yin:,:]*drF_exp*rA_exp
  ShelfVolume_exp = np.expand_dims(ShelfVolume,0)
  ShelfVolume_exp = ShelfVolume_exp + np.zeros(HighConc_Mask.shape)
    
  HighConc_CellVol = np.ma.masked_array(ShelfVolume_exp,mask = HighConc_Mask) 
  VolWaterHighConc = np.ma.sum(np.ma.sum(np.ma.sum(HighConc_CellVol,axis = 1),axis=1),axis=1)
    
   #Get total mass of tracer on shelf
  Total_Tracer = np.ma.sum(np.ma.sum(np.ma.sum(ShelfVolume_exp*TrMask[:,:zfin,yin:,:]*1000.0,axis = 1),axis=1),axis=1) 
   # 1 m^3 = 1000 l
    
  return (VolWaterHighConc, Total_Tracer)
 

 # ------------------------------------------------------------------------------------------------------------------------
def calc_HCW(Tr,MaskC,rA,hFacC,drF,nzlim=29,yin=227,zfin=29,xi=180,yi=50):
  '''
  INPUT----------------------------------------------------------------------------------------------------------------
    Tr    : Array with concentration values for a tracer. Until this function is more general, this should be size 19x90x360x360
    MaskC : Land mask for tracer
    nzlim : The nz index under which to look for water properties
    rA    : Area of cell faces at C points (360x360)
    fFacC : Fraction of open cell (90x360x360)
    drF   : Distance between cell faces (90)
    yin   : across-shore index of shelf break
    zfin  : shelf break index + 1 
    xi    : initial profile x index
    yi    : initial profile y index
      
    All dimensions should match.
   
   OUTPUT----------------------------------------------------------------------------------------------------------------
    VolWaterHighConc =  np array with the volume of water with concentration equal or higher than the concentration at Z[nzlim]
    in the initial volume defined by the dimensions of Tr at every time output.
  -----------------------------------------------------------------------------------------------------------------------
  '''
  maskExp = maskExpand(MaskC,Tr)

  TrMask=np.ma.array(Tr,mask=maskExp)   
    
  trlim = TrMask[0,nzlim,yi,xi]
    
  print('tracer limit concentration is: ',trlim)
    
  WaterX = 0
    
  # mask cells with tracer concentration < trlim on shelf
  HighConc_Masked = np.ma.masked_less(TrMask[:,:zfin,yin:,:], trlim) 
  HighConc_Mask = HighConc_Masked.mask
    
  #Get volume of water of cells with relatively high concentration
  rA_exp = np.expand_dims(rA[yin:,:],0)
  drF_exp = np.expand_dims(np.expand_dims(drF[:zfin],1),1)
  rA_exp = rA_exp + np.zeros(hFacC[:zfin,yin:,:].shape)
  drF_exp = drF_exp + np.zeros(hFacC[:zfin,yin:,:].shape)
    
  ShelfVolume = hFacC[:zfin,yin:,:]*drF_exp*rA_exp
  ShelfVolume_exp = np.expand_dims(ShelfVolume,0)
  ShelfVolume_exp = ShelfVolume_exp + np.zeros(HighConc_Mask.shape)
    
  HighConc_CellVol = np.ma.masked_array(ShelfVolume_exp,mask = HighConc_Mask) 
  VolWaterHighConc = np.ma.sum(np.ma.sum(np.ma.sum(HighConc_CellVol,axis = 1),axis=1),axis=1)
    
  return (VolWaterHighConc)
 
 # ---------------------------------------------------------------------------------------------------------------------------

  # ------------------------------------------------------------------------------------------------------------------------
def calc_TrMassonShelf(Tr,MaskC,rA,hFacC,drF,yin=227,zfin=29):
  '''
  INPUT----------------------------------------------------------------------------------------------------------------
    Tr    : Array with concentration values for a tracer. Until this function is more general, this should be size 19x90x360x360
    MaskC : Land mask for tracer
    rA    : Area of cell faces at C points (360x360)
    fFacC : Fraction of open cell (90x360x360)
    drF   : Distance between cell faces (90)
    yin   : across-shore index of shelf break
    zfin  : shelf break index + 1 
    
   All dimensions should match.
   
   OUTPUT----------------------------------------------------------------------------------------------------------------
    Total_Tracer =  np array with the mass of tracer on shelf at every time output.
  -----------------------------------------------------------------------------------------------------------------------
  '''
  maskExp = maskExpand(MaskC,Tr)

  TrMask=np.ma.array(Tr,mask=maskExp)   
    
  rA_exp = np.expand_dims(rA[yin:,:],0)
  drF_exp = np.expand_dims(np.expand_dims(drF[:zfin],1),1)
  rA_exp = rA_exp + np.zeros(hFacC[:zfin,yin:,:].shape)
  drF_exp = drF_exp + np.zeros(hFacC[:zfin,yin:,:].shape)
    
  ShelfVolume = hFacC[:zfin,yin:,:]*drF_exp*rA_exp
  ShelfVolume_exp = np.expand_dims(ShelfVolume,0)
  ShelfVolume_exp = ShelfVolume_exp + np.zeros(HighConc_Mask.shape)
    
   #Get total mass of tracer on shelf
  Total_Tracer = np.ma.sum(np.ma.sum(np.ma.sum(ShelfVolume_exp*TrMask[:,:zfin,yin:,:]*1000.0,axis = 1),axis=1),axis=1) 
   # 1 m^3 = 1000 l 
  return (Total_Tracer)
 
 
# ------------------------------------------------------------------------------------------------------------------------
def calc_ShelfVolume(rA,hFacC,drF,yin=227,zfin=29s):
  '''
  INPUT----------------------------------------------------------------------------------------------------------------
    
    rA    : Area of cell faces at C points (360x360)
    fFacC : Fraction of open cell (90x360x360)
    drF   : Distance between cell faces (90)
    yin   : across-shore index of shelf break
    zfin  : shelf break index + 1 
   
    All dimensions should match.
   
   OUTPUT----------------------------------------------------------------------------------------------------------------
    ShelfVolume =  Volume of shelf
  -----------------------------------------------------------------------------------------------------------------------
  '''
    
  rA_exp = np.expand_dims(rA[yin:,:],0)
  drF_exp = np.expand_dims(np.expand_dims(drF[:zfin],1),1)
  rA_exp = rA_exp + np.zeros(hFacC[:zfin,yin:,:].shape)
  drF_exp = drF_exp + np.zeros(hFacC[:zfin,yin:,:].shape)
    
  ShelfVolume = hFacC[:zfin,yin:,:]*drF_exp*rA_exp
      
  return (ShelfVolume)
 
 # ---------------------------------------------------------------------------------------------------------------------------

 def howMuchWaterCV(Tr,MaskC,nzlim,rA,hFacC,drF,yin,zfin,xi,yi,xo,xf):
  '''
  INPUT----------------------------------------------------------------------------------------------------------------
    Tr    : Array with concentration values for a tracer. Until this function is more general, this should be size 19x90x360x360
    MaskC : Land mask for tracer
    nzlim : The nz index under which to look for water properties
    rA    : Area of cell faces at C points (360x360)
    fFacC : Fraction of open cell (90x360x360)
    drF   : Distance between cell faces (90)
    yin   : across-shore index of shelf break
    zfin  : shelf break index + 1 
    xi    : initial profile x index
    yi    : initial profile y index
    xo,xf : x indices of control volume
    OUTPUT----------------------------------------------------------------------------------------------------------------
    VolWaterHighConc =  Array with the volume of water over the shelf wothout the cube on top of the canyon at every time output.
    Total_Tracer =  Array with the mass of tracer (m^3*[C]*l/m^3) at each x-position over the shelf [:,:30,227:,:] at 
                    every time output. Total mass of tracer at xx on the shelf without the cube on top of the canon.
                                                
  -----------------------------------------------------------------------------------------------------------------------
  '''
  maskExp = maskExpand(MaskC,Tr)

  TrMask=np.ma.array(Tr,mask=maskExp)   
    
  trlim = TrMask[0,nzlim,yi,xi]
    
  print('tracer limit concentration is: ',trlim)
    
  WaterX = 0
    
  # mask cells with tracer concentration < trlim on shelf
  HighConc_Masked = np.ma.masked_less(TrMask[:,:zfin,yin:,xo:xf], trlim) 
  HighConc_Mask = HighConc_Masked.mask
    
  #Get volume of water of cells with relatively high concentration
  rA_exp = np.expand_dims(rA[yin:,xo:xf],0)
  drF_exp = np.expand_dims(np.expand_dims(drF[:zfin],1),1)
  rA_exp = rA_exp + np.zeros(hFacC[:zfin,yin:,xo:xf].shape)
  drF_exp = drF_exp + np.zeros(hFacC[:zfin,yin:,xo:xf].shape)
    
  ShelfVolume = hFacC[:zfin,yin:,xo:xf]*drF_exp*rA_exp
  ShelfVolume_exp = np.expand_dims(ShelfVolume,0)
  ShelfVolume_exp = ShelfVolume_exp + np.zeros(HighConc_Mask.shape)
    
  HighConc_CellVol = np.ma.masked_array(ShelfVolume_exp,mask = HighConc_Mask) 
  VolWaterHighConc = np.ma.sum(np.ma.sum(np.ma.sum(HighConc_CellVol,axis = 1),axis=1),axis=1)
    
   #Get total mass of tracer on shelf
  Total_Tracer = np.ma.sum(np.ma.sum(np.ma.sum(ShelfVolume_exp*TrMask[:,:zfin,yin:,xo:xf]*1000.0,axis = 1),axis=1),axis=1) 
   # 1 m^3 = 1000 l
    
  return (VolWaterHighConc, Total_Tracer)
  
  
  
#---------------------------------------------------------------------------------------------------------------------------
def howMuchWaterShwHole(Tr,MaskC,nzlim,rA,hFacC,drF,yin,zfin,xi,yi,xh1=120,xh2=240,yh1=227,yh2=267):
  '''
    INPUT----------------------------------------------------------------------------------------------------------------
    Tr    : Array with concentration values for a tracer. Until this function is more general, this should be size 19x90x360x360
    MaskC : Land mask for tracer
    nzlim : The nz index under which to look for water properties
    rA    : Area of cell faces at C points (360x360)
    fFacC : Fraction of open cell (90x360x360)
    drF   : Distance between cell faces (90)
    yin   : across-shore index of shelf break
    zfin  : shelf break index + 1 
    xi    : initial profile x index
    yi    : initial profile y index
    xh1=120 : 1st x index of hole (defaults are the definitions used for transport calculations)
    xh2=240 : 2nd x index of hole
    yh1=227 : 1st y index of hole
    yh2=267 : 2nd y index of hole
    
    OUTPUT----------------------------------------------------------------------------------------------------------------
    VolWaterHighConc =  Array with the volume of water over the shelf [:,:30,227:,:] at every time output.
    Total_Tracer =  Array with the mass of tracer (m^3*[C]*l/m^3) at each x-position over the shelf [:,:30,227:,:] at 
                    every time output. Total mass of tracer at xx on the shelf.
    VolWaterHighConcHole =  Array with the volume of water insde cube at every time output.
    Total_TracerHole =  Array with the mass of tracer inside hole.
                                               
    -----------------------------------------------------------------------------------------------------------------------
  '''
  maskExp = maskExpand(MaskC,Tr)

  TrMask=np.ma.array(Tr,mask=maskExp)   
    
  trlim = TrMask[0,nzlim,yi,xi]
    
  print('tracer limit concentration is: ',trlim)
    
  
  # mask cells with tracer concentration < trlim on control volume
  HighConc_Masked = np.ma.masked_less(TrMask[:,:zfin,yin:,:], trlim) 
  HighConc_Mask = HighConc_Masked.mask
    
  HighConcHole_Masked = np.ma.masked_less(TrMask[:,:zfin,yh1:yh2,xh1:xh2], trlim) 
  HighConcHole_Mask = HighConcHole_Masked.mask
  
  
  #Get volume of water of cells with relatively high concentration
  rA_exp = np.expand_dims(rA[yin:,:],0)
  rA_exp_hole = np.expand_dims(rA[yh1:yh2,xh1:xh2],0)
  
  rA_exp = rA_exp + np.zeros(hFacC[:zfin,yin:,:].shape)
  rA_exp_hole = rA_exp_hole + np.zeros(hFacC[:zfin,yh1:yh2,xh1:xh2].shape)
 
  drF_exp = np.expand_dims(np.expand_dims(drF[:zfin],1),1)
  drF_exp_hole = np.expand_dims(np.expand_dims(drF[:zfin],1),1)
  
  drF_exp = drF_exp + np.zeros(hFacC[:zfin,yin:,:].shape)
  drF_exp_hole = drF_exp_hole +np.zeros(hFacC[:zfin,yh1:yh2,xh1:xh2].shape)
  
   
  ShelfVolume = hFacC[:zfin,yin:,:]*drF_exp*rA_exp
  ShelfVolume_exp = np.expand_dims(ShelfVolume,0)
  ShelfVolume_exp = ShelfVolume_exp + np.zeros(HighConc_Mask.shape)
    
  HoleVolume = hFacC[:zfin,yh1:yh2,xh1:xh2]*drF_exp_hole*rA_exp_hole
  HoleVolume_exp = np.expand_dims(HoleVolume,0)
  HoleVolume_exp = HoleVolume_exp + np.zeros(HighConcHole_Mask.shape)
  
  
  HighConc_CellVol = np.ma.masked_array(ShelfVolume_exp,mask = HighConc_Mask) 
  HighConc_CellVol_Hole = np.ma.masked_array(HoleVolume_exp,mask = HighConcHole_Mask) 
  
  VolWaterHighConc = np.ma.sum(np.ma.sum(np.ma.sum(HighConc_CellVol,axis = 1),axis=1),axis=1)
  VolWaterHighConcHole = np.ma.sum(np.ma.sum(np.ma.sum(HighConc_CellVol_Hole,axis = 1),axis=1),axis=1)
  
  VolWaterHighConcShelfwHole = VolWaterHighConc-VolWaterHighConcHole
  
  #Get total mass of tracer on shelf
  Total_Tracer = np.ma.sum(np.ma.sum(np.ma.sum(ShelfVolume_exp*TrMask[:,:zfin,yin:,:]*1000.0,axis = 1),axis=1),axis=1) 
  Total_Tracer_Hole = np.ma.sum(np.ma.sum(np.ma.sum(HoleVolume_exp*TrMask[:,:zfin,yh1:yh2,xh1:xh2]*1000.0,axis = 1),axis=1),axis=1) 
  
  Total_Tracer_ShelfwHole = Total_Tracer-Total_Tracer_Hole
  
  # 1 m^3 = 1000 l
    
  return (VolWaterHighConcShelfwHole, Total_Tracer_ShelfwHole,VolWaterHighConcHole,Total_Tracer_Hole)


#----------------------------------------------------------------------------------------------------------------------------

def get_TRAC(fluxFile, keyW, keyV, keyU):
  ''' all input are strings'''
  WTRAC = rout.getField(fluxFile,keyW)
  UT = rout.getField(fluxFile,keyU)
  VT = rout.getField(fluxFile,keyV)
  UTRAC,VTRAC = rout.unstagger(UT,VT)
    
  return (WTRAC, VTRAC, UTRAC)

#----------------------------------------------------------------------------------------------------------------------------

def slice_TRAC(field,i1,i2,j1,j2,k1,k2,t1,t2):
  '''i1 initial x index, i2 final x index and so on. Integers. Returns sliced field'''
  if i1 == i2:
    sl = field[t1:t2,k1:k2,j1:j2,i1]
  elif j1==j2:
    sl = field[t1:t2,k1:k2,j1,i1:i2]
  elif k1 == k2:
    sl = field[t1:t2,k1,j1:j2,i1:i2]
  elif t1 == t2:
    sl = field[t1,k1:k2,j1:j2,i1:i2]
  else:
    sl = field[t1:t2,k1:k2,j1:j2,i1:i2]
  
  return sl
  
#---------------------------------------------------------------------------------------------------------------------------------  
  
def slice_area(dx,dr,rA,hFacC,i1,i2,j1,j2,k1,k2):
  '''i1,j1,k1 initial indices of slice, i2,j2,k2 final indices. dx is dy when the slice is AS1 or AS2.'''
  if i1 == i2:
    
    dr_exp = np.expand_dims(dr[k1:k2],1)
    dr_exp = dr_exp + np.zeros(hFacC[k1:k2,j1:j2,i1].shape)
  
    dx_exp = np.expand_dims(dx[j1:j2,i1],0)
    dx_exp = dx_exp + np.zeros(hFacC[k1:k2,j1:j2,i1].shape)
    
    area = hFacC[k1:k2,j1:j2,i1]*dx_exp*dr_exp
  
  
  elif j1==j2:
    
    dr_exp = np.expand_dims(dr[k1:k2],1)
    dr_exp = dr_exp + np.zeros(hFacC[k1:k2,j1,i1:i2].shape)
  
    dx_exp = np.expand_dims(dx[j1,i1:i2],0)
    dx_exp = dx_exp + np.zeros(hFacC[k1:k2,j1,i1:i2].shape)
   
    area = hFacC[k1:k2,j1,i1:i2]*dx_exp*dr_exp
  
  else:
    
    rA_exp = np.expand_dims(rA[j1:j2,i1:i2],0)
  
    rA_exp = rA_exp + np.zeros(hFacC[k1,j1:j2,i1:i2].shape)
  
    area = hFacC[k1,j1:j2,i1:i2]*rA_exp
  
  return area
  
#---------------------------------------------------------------------------------------------------------------------------------  
  
 #---------------------------------------------------------------------------------------------------------------------------
def Volume_Sh_and_Hole(MaskC,rA,hFacC,drF,yin,zfin,xh1=120,xh2=240,yh1=227,yh2=267):
  '''
    INPUT----------------------------------------------------------------------------------------------------------------
    MaskC : Land mask for tracer
     rA    : Area of cell faces at C points (360x360)
    fFacC : Fraction of open cell (90x360x360)
    drF   : Distance between cell faces (90)
    yin   : across-shore index of shelf break
    zfin  : shelf break index + 1 
    xh1=120 : 1st x index of hole (defaults are the definitions used for transport calculations)
    xh2=240 : 2nd x index of hole
    yh1=227 : 1st y index of hole
    yh2=267 : 2nd y index of hole
    
    OUTPUT----------------------------------------------------------------------------------------------------------------
    Canyon box volume and Shelf with hole volume                                           
    -----------------------------------------------------------------------------------------------------------------------
  '''
   
  rA_exp = np.expand_dims(rA[yin:,:],0)
  rA_exp_hole = np.expand_dims(rA[yh1:yh2,xh1:xh2],0)
  
  rA_exp = rA_exp + np.zeros(hFacC[:zfin,yin:,:].shape)
  rA_exp_hole = rA_exp_hole + np.zeros(hFacC[:zfin,yh1:yh2,xh1:xh2].shape)
 
  drF_exp = np.expand_dims(np.expand_dims(drF[:zfin],1),1)
  drF_exp_hole = np.expand_dims(np.expand_dims(drF[:zfin],1),1)
  
  drF_exp = drF_exp + np.zeros(hFacC[:zfin,yin:,:].shape)
  drF_exp_hole = drF_exp_hole +np.zeros(hFacC[:zfin,yh1:yh2,xh1:xh2].shape)
  
   
  ShelfVolume = hFacC[:zfin,yin:,:]*drF_exp*rA_exp
  HoleVolume = hFacC[:zfin,yh1:yh2,xh1:xh2]*drF_exp_hole*rA_exp_hole
  
 
  #Get total mass of tracer on shelf
  Total_Vol = np.ma.sum(ShelfVolume) 
  Total_Vol_Hole = np.ma.sum(HoleVolume) 
  
  Total_Vol_ShelfwHole = Total_Vol-Total_Vol_Hole
  
  # 1 m^3 = 1000 l
    
  return (Total_Vol_ShelfwHole,Total_Vol_Hole)

 
  
def maskHC(targetConc,tracer,i1,i2,j1,j2,k1,k2,t1,t2):
  '''INPUT
     targetConc : threshold concentration to mask if cell conecntration is lower than.
     Tracer: tracer  field size [nt,nz,ny,nx] 
     i1 initial x index, i2 final x index and so on. Integers. 
     OUTPUT
     Returns: Mask (true for cells with concntration larger or equal than targerConc.)'''
  
  
  if i1 == i2:
    sl = tracer[t1:t2,k1:k2,j1:j2,i1]
  elif j1==j2:
    sl = tracer[t1:t2,k1:k2,j1,i1:i2]
  elif k1 == k2:
    sl = tracer[t1:t2,k1,j1:j2,i1:i2]
  elif t1 == t2:
    sl = tracer[t1,k1:k2,j1:j2,i1:i2]
  else:
    sl = tracer[t1:t2,k1:k2,j1:j2,i1:i2]
  
  slice_masked = np.ma.masked_less(sl, targetConc) 
  slice_Mask = slice_masked.mask
  
  return slice_Mask
  
  

