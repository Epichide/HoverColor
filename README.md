"# HoverColor" 

# HoverColor

example

![20250427011134](README/20250727011134.png)

## Usage

* pixel hover color : ctrl + `
* custom hover color : shift + `
* hover range : 
    up : ctrl + 1
    down : ctrl + 2
    reset : ctrl + 0

## update log
- 20250813
  - add YUV,YCbcr,YPbPr
  - YUV, YCbCr, and YPbPr all belong to the YUV color model (the YUV model also includes a transformed version called YUV, which is derived from PAL). 
  - YUV and YPbPr share similar transformation principles. YPbPr, developed after YUV, is specifically designed for digital display devices. YUV ranges from (Y: 0, U:-0.436,V: -0.615) to (Y: 1, U:0.436,V: 0.615)
  - YCbCr is a digital format based on YPbPr. In terms of value ranges, YPbPr ranges from (Y: 0, Pb/Pr: -0.5) to (Y: 1, Pb/Pr: 0.5), whereas YCbCr ranges from (Y: 16, Cb/Cr: 16) to (Y: 235, Cb/Cr: 240)
    - ref : 
      - [wiki:YCbCr](https://en.wikipedia.org/wiki/YCbCr#R'G'B'_to_Y%E2%80%B2PbPr)
      - [wki:YUV](https://en.wikipedia.org/wiki/Y%E2%80%B2UV)
      - [YCbCr - YPbPr](https://fujiwaratko.sakura.ne.jp/infosci/colorspace/colorspace4_e.html)
- 20250810
  - Custom Record
  - Parse and load ICC profile 
    - What is chad?
      - [ICC Technical Note 02-2003 Chadtag for conversion of D65 to D50 for use in profiles](https://www.color.org/chadtag.xalter)
      - [Why is "Display P3 - Green Primary" different from the ICC profile?](https://github.com/colour-science/colour/discussions/739)
    - ICC display ICC use Bradford Chromatic Adaptation
      - [Bradford Chromatic Adaptation](http://www.brucelindbloom.com/index.html?Eqn_ChromAdapt.html)
      - [https://www.color.org/chadtag.xalter](https://www.color.org/chadtag.xalter)
    - Why display ICC use D50 PCS Illuminant:
      - [ICC Profile Format](https://www.color.org/specification/ICC1v43_2010-12.pdf) : "The PCS is based on the CIE 1931 XYZ color space with a D50 illuminant."
      - [Why D50?](https://www.color.org/whyd50.xalter)
      - [The Reference White in Adobe Photoshop Lab Mode](https://color-image.com/2011/10/the-reference-white-in-adobe-photoshop-lab-mode/)
      - [ICC’s D50 vs sRGB D65 problems](https://discuss.pixls.us/t/iccs-d50-vs-srgb-d65-problems/11134)
    - parse ICC to get RGB2XYZ and WP_Illuminant: 
      - [Why is "Display P3 - Green Primary" different from the ICC profile?](https://github.com/colour-science/colour/discussions/739)
      - [ICC Profile Format](https://www.color.org/specification/ICC1v43_2010-12.pdf) : "The PCS is based on the CIE 1931 XYZ color space with a D50 illuminant."
    - Load and parse ICC: forked from [iccinspector.py](https://github.com/sobotka/iccinspector)
- 20250725:
  - adaptive resolution and size
- 20250719:
  - add BT2020 BT09 gamut
  - TODO : JCH support different gamut
  - add XYZ color space and [xy chromaticity diagram](https://github.com/ZhaJiMan/do_color)
- 20250717:
  - fix bug: RGB value display error: G=Gray : fixed
  - add new gamut ( only work on Lab colorspace): P3-D65(displayP3), sRGB, P3-DCI
  - remember last used profile, auto load last profile
  - **TODO : Reset profile**
- 20250717:
  - global hotkey setting
  - fix delta2020 -> 2000
  - **TODO : add some restricts for key binding**
- 20250715:
  - support : AutoAdjust Scaling when screen resolution changes
  - fix bug : multi screen crash : move from one screen to another
  - support : minimize and restore widget
- 20250712：
  - adjust colorwidget angle : red is on top-right
  - add [deltaE(2000)](https://github.com/lovro-i/CIEDE2000/blob/master/ciede2000.py)
  - add RGB+G record
  - **TODO : icc profile**
  - **TODO :more deltaE formula**
- 20250710:
    - add custom [screenashot](https://github.com/SeptemberHX/screenshot) color picker (average) : shift + `
    - add custom hover color picker size(average) : 
      - zoon in : ctrl + 1
      - zoon out : ctrl + 2
      - reset : ctrl + 0
    - widget layout adapted to widgets number
    - colorspace menuitems are moved to subfolder
- 20250410:
    - add custom hover color picker (point) : ctrl + `
    - show or hide any colorspace widget
    - switch to different color value recoder
    - 
