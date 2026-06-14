# ICC Conversion Chain Figures

This directory contains JPG figures cropped from `ICC Specification format-2022-05.pdf`.

The figures are used to explain ICC transform chains. They are not parsed results from a specific ICC file.

## 1. Basic mapping

```text
A = data colour space / device space / color encoding space
B = PCS = Profile Connection Space

AToB = A -> B = Device / Color Encoding -> PCS
BToA = B -> A = PCS -> Device / Color Encoding
```

Typical examples:

```text
AToB: RGB / CMYK / nCLR -> PCSXYZ or PCSLab
BToA: PCSXYZ or PCSLab -> RGB / CMYK / nCLR
```

## 2. Common blocks in the figures

```text
TRC    = Tone Reproduction Curve, one-dimensional tone curve
Matrix = matrix transform, often used by RGB <-> PCSXYZ models
CLUT   = Colour Lookup Table, multi-dimensional nonlinear lookup table
A curves = one-dimensional curves near the A side
B curves = one-dimensional curves near the B side
M curves = middle one-dimensional curves in LUT chains
multiProcessElementsType = ordered processing-element chain
```

## 3. Figure groups

```text
Figure 2: PCS -> Device space
          usually corresponds to BToA / lutBToAType

Figure 3: Device space -> PCS
          usually corresponds to AToB / lutAToBType

Figure 5: Device -> Device
          usually corresponds to DeviceLink profile transforms
```

## 4. Figure 2: PCS -> Device space

### figure2a_pcs_to_device_matrix_trc.jpg

```text
PCSXYZ -> Matrix inverse / matrix-based transform -> inverse TRC -> Device RGB
```

### figure2b_pcs_to_device_lutBToA.jpg

```text
PCS -> "B" curves -> Matrix -> "M" curves -> "A" curves -> Device space
```

### figure2c_pcs_to_device_lutBToA.jpg

```text
PCS -> "B" curves -> CLUT -> "A" curves -> Device space
```

### figure2d_pcs_to_device_lutBToA.jpg

```text
PCS -> "B" curves -> CLUT -> "A" curves -> Device space channels 1..n
```

Example:

```text
PCSLab -> "B" curves -> CLUT -> "A" curves -> CMYK / nCLR
```

### figure2e_pcs_to_device_lutBToA.jpg

```text
PCS -> "B" curves -> Matrix -> "M" curves -> CLUT -> "A" curves -> Device space
```

### figure2f_pcs_to_device_multiProcessElements.jpg

```text
PCS -> Process Element 1 -> Process Element 2 -> ... -> Process Element n -> Device space
```

## 5. Figure 3: Device space -> PCS

### figure3a_device_to_pcs_matrix_trc.jpg

```text
Device RGB -> TRC -> Matrix -> PCSXYZ
```

### figure3b_device_to_pcs_lutAToB.jpg

```text
Device space -> "A" curves -> Matrix -> "M" curves -> "B" curves -> PCS
```

### figure3c_device_to_pcs_lutAToB.jpg

```text
Device space -> "A" curves -> CLUT -> "B" curves -> PCS
```

### figure3d_device_to_pcs_lutAToB.jpg

```text
Device space channels 1..n -> "A" curves -> CLUT -> "B" curves -> PCS
```

Example:

```text
CMYK / nCLR -> "A" curves -> CLUT -> "B" curves -> PCSLab
```

### figure3e_device_to_pcs_lutAToB.jpg

```text
Device space -> "A" curves -> CLUT -> "M" curves -> Matrix -> "B" curves -> PCS
```

### figure3f_device_to_pcs_multiProcessElements.jpg

```text
Device space -> Process Element 1 -> Process Element 2 -> ... -> Process Element n -> PCS
```

## 6. Figure 5: Device -> Device / DeviceLink

DeviceLink profile can pre-compose a normal ICC chain:

```text
Source Device -> PCS -> Destination Device
```

into a direct chain:

```text
Source Device -> Destination Device
```

### figure5a_device_to_device_trc.jpg

```text
Source device channel -> TRC -> Destination device channel
```

### figure5b_device_to_device_matrix_trc.jpg

```text
Source device channels -> TRC -> Matrix -> Destination device channels
```

### figure5c_device_to_device_clut_trc.jpg

```text
Source device channels -> CLUT -> TRC -> Destination device channels
```

### figure5d_device_to_device_clut_matrix_trc.jpg

```text
Source device channels -> CLUT -> Matrix -> TRC -> Destination device channels
```

### figure5e_device_to_device_multiProcessElements.jpg

```text
Source device space -> Process Element 1 -> Process Element 2 -> ... -> Process Element n -> Destination device space
```

## 7. Relation to Profile Class

```text
scnr = Input profile       = usually Device -> PCS
mntr = Display profile     = usually Device <-> PCS
prtr = Output profile      = usually Device <-> PCS
spac = ColorSpace profile  = usually Color Encoding <-> PCS
link = DeviceLink profile  = Device -> Device
```

## 8. Direction quick rules

```text
AToB / DToB = Device or Color Encoding -> PCS
BToA / BToD = PCS -> Device or Color Encoding
Matrix/TRC  = common for RGB <-> PCSXYZ
DeviceLink  = Source Device -> Destination Device
```

## 9. Original crop info

| File | PDF page | Crop box |
|---|---:|---|
| `figure2a_pcs_to_device_matrix_trc.jpg` | 9 | `(60.0, 370.0, 535.0, 492.0)` |
| `figure2b_pcs_to_device_lutBToA.jpg` | 9 | `(60.0, 495.0, 535.0, 616.0)` |
| `figure2c_pcs_to_device_lutBToA.jpg` | 9 | `(60.0, 620.0, 535.0, 740.0)` |
| `figure2d_pcs_to_device_lutBToA.jpg` | 10 | `(55.0, 55.0, 535.0, 210.0)` |
| `figure2e_pcs_to_device_lutBToA.jpg` | 10 | `(55.0, 215.0, 535.0, 355.0)` |
| `figure2f_pcs_to_device_multiProcessElements.jpg` | 10 | `(55.0, 365.0, 535.0, 475.0)` |
| `figure3a_device_to_pcs_matrix_trc.jpg` | 10 | `(55.0, 505.0, 535.0, 645.0)` |
| `figure3b_device_to_pcs_lutAToB.jpg` | 10 | `(55.0, 650.0, 535.0, 770.0)` |
| `figure3c_device_to_pcs_lutAToB.jpg` | 11 | `(55.0, 55.0, 535.0, 190.0)` |
| `figure3d_device_to_pcs_lutAToB.jpg` | 11 | `(55.0, 195.0, 535.0, 335.0)` |
| `figure3e_device_to_pcs_lutAToB.jpg` | 11 | `(55.0, 340.0, 535.0, 482.0)` |
| `figure3f_device_to_pcs_multiProcessElements.jpg` | 11 | `(55.0, 485.0, 535.0, 603.0)` |
| `figure5a_device_to_device_trc.jpg` | 13 | `(60.0, 130.0, 535.0, 240.0)` |
| `figure5b_device_to_device_matrix_trc.jpg` | 13 | `(60.0, 245.0, 535.0, 365.0)` |
| `figure5c_device_to_device_clut_trc.jpg` | 13 | `(60.0, 395.0, 535.0, 535.0)` |
| `figure5d_device_to_device_clut_matrix_trc.jpg` | 13 | `(60.0, 535.0, 535.0, 680.0)` |
| `figure5e_device_to_device_multiProcessElements.jpg` | 14 | `(55.0, 45.0, 535.0, 100.0)` |



## 10. Direction determination


转换方向判断流程
转换方向：Device → PCS、PCS → Device、双向
你可以按这个顺序判断：
1. 读取 Header
   - profile_class
   - data_colour_space
   - PCS

2. 读取 Tag Table
   - 看是否有 AToB*
   - 看是否有 BToA*
   - 看是否有 DToB*
   - 看是否有 BToD*
   - 看是否有 Matrix/TRC tag
   - 看是否有 grayTRC

3. 根据 tag 判断可用方向
   - AToB* 或 DToB* 存在：Device / Color Encoding → PCS
   - BToA* 或 BToD* 存在：PCS → Device / Color Encoding
   - 两类都存在：双向
   - Matrix/TRC 存在：通常 RGB → PCS；可逆时工程上可反向
   - grayTRC 存在：通常 Gray → PCS；可逆时工程上可反向

4. 再结合 profile_class 判断语义
   - scnr：偏 Device → PCS
   - mntr：偏 Device ↔ PCS
   - prtr：偏 Device ↔ PCS
   - spac：偏 Color Encoding ↔ PCS



## matix

```
[Y1]   [e1 e2 e3]   [X1]   [e10]
[Y2] = [e4 e5 e6] * [X2] + [e11]
[Y3]   [e7 e8 e9]   [X3]   [e12]
```