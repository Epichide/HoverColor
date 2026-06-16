lutAToBType:
"This structure represents a colour transform. The type contains up to five processing elements which are stored in the AToBTag tag in the following order: a set of one-dimensional curves, a 3 ´ 3 matrix with offset terms, a set of one-dimensional curves, a multi-dimensional lookup table, and a set of one-dimensional output curves. Data are processed using these elements via the following sequence:

(sf^Lambda^curves)⇒(multi-dimensionalolobup table, CLUT)⇒(CM^curves)⇒(manti)⇒(CB^curves).

NOTE The processing elements are not in this order in the tag to allow for simplified reading and writing of profiles.

It is possible to use any or all of these processing elements. At least one processing element shall be included.
Only the following combinations are permitted:

B;
M, Matrix, B;
A, CLUT, B;
A, CLUT, M, Matrix, B.

Other combinations can be achieved by setting processing element values to identity transforms. The domain and range of the A and B curves and CLUT are defined to consist of all real numbers between 0,0 and 1,0 inclusive. The first entry is located at 0,0, the last entry at 1,0, and intermediate entries are uniformly spaced using an increment of 1,0/(m-1). For the A and B curves, m is the number of entries in the table. For the CLUT, m is the number of grid points along each dimension. Since the domain and range of the tables are 0,0 to 1,0 it is necessary to convert all device values and PCSLAB values to this numeric range. It shall be assumed that the maximum value in each case is set to 1,0 and the minimum value to 0,0 and all intermediate values are linearly scaled accordingly."

The "M" curves are described as:
"There are the same number of “M” curves as there are output channels. The curves are stored sequentially, with 00h bytes used for padding between them if needed. Each “M” curve is stored as an embedded curveType or a parametricCurveType (see 10.5 or 10.16). The length is as indicated by the convention of the respective curve type. Note that the entire tag type, including the tag type signature and reserved bytes, are included for each curve. The “M” curves may only be used when the matrix is used."

The matrix is described as:
"The matrix is organized as a 3 ´ 4 array. The elements of the matrix appear in the type in order from e1 to e12. The matrix elements are each s15Fixed16Numbers.

array=[e1,e2,e3,e4,e5,e6,e7,e8,e9,e10,e11,e12]

The matrix is used to convert data to a different colour space, according to the following equation:

Y1 = [e11 e12 e13 e14 e15 e16 e17 e18 e19 e110 e111 e112] * X1
Y2 = [e21 e22 e23 e24 e25 e26 e27 e28 e29 e210 e211 e212] * X2
...
Yq = [eq1 eq2 eq3 eq4 eq5 eq6 eq7 eq8 eq9 eq10 eq11 eq12] * Xq

The range of input values X1, X2, ..., Xq is 0,0 to 1,0. The resultant values Y1, Y2, ..., Yq shall be clipped to the range 0,0 to 1,0 and used as inputs to the “B” curves.

The matrix is permitted only if the number of output channels, or “M” curves, is 3."

The offsets to the processing elements are:
"The offset entries (bytes 12 to 31) point to the various processing elements found in the tag. The offsets indicate the number of bytes from the beginning of the tag to the desired data. If any of the offsets are zero, i.e. an indication that processing element is not present and the operation is not performed."

lutBToAType:
"This structure represents a colour transform. The type contains up to five processing elements which are stored in the BToATag tag in the following order: a set of one-dimensional curves, a 3 ´ 3 matrix with offset terms, a set of one-dimensional curves, a multi-dimensional lookup table, and a set of one-dimensional output curves. Data are processed using these elements via the following sequence:

(B curves)⇒(Matrix)⇒(M curves)⇒(CLUT)⇒(A curves).

NOTE The processing elements are not in this order in the tag to allow for simplified reading and writing of profiles.

It is possible to use any or all of these processing elements. At least one processing element shall be included.
Only the following combinations are permitted:

B;
B, Matrix, M;
B, CLUT, A;
B, Matrix, M, CLUT, A.

Other combinations can be achieved by setting processing element values to identity transforms. The domain and range of the A and B curves and CLUT are defined to consist of all real numbers between 0,0 and 1,0 inclusive. The first entry is located at 0,0, the last entry at 1,0, and intermediate entries are uniformly spaced using an increment of 1,0/(m-1). For the A, M and B curves m is the number of entries in the table. For the CLUT, m is the number of grid points along each dimension. Since the domain and range of the tables are 0,0 to 1,0 it is necessary to convert all device values and PCSLAB values to this numeric range. It shall be assumed that the maximum value in each case is set to 1,0 and the minimum value to 0,0 and all intermediate values are linearly scaled accordingly."

The matrix is described as:
"The matrix is organized as a 3 ´ 4 array. The elements of the matrix appear in the type in order from e1 to e12. The matrix elements are each s15Fixed16Numbers.

array=[e1,e2,e3,e4,e5,e6,e7,e8,e9,e10,e11,e12]

The matrix is used to convert data to a different colour space, according to the following equation:

Y1 = [e11 e12 e13 e14 e15 e16 e17 e18 e19 e110 e111 e112] * X1
Y2 = [e21 e22 e23 e24 e25 e26 e27 e28 e29 e210 e211 e212] * X2
...
Yq = [eq1 eq2 eq3 eq4 eq5 eq6 eq7 eq8 eq9 eq10 eq11 eq12] * Xq

The range of input values X1, X2, ..., Xq is 0,0 to 1,0. The resultant values Y1, Y2, ..., Yq shall be clipped to the range 0,0 to 1,0 and used as inputs to the “M” curves.

The matrix is permitted only if the number of output channels, or “M” curves, is 3."

The offsets to the processing elements are:
"The offset entries (bytes 12 to 31) point to the various processing elements found in the tag. The offsets indicate the number of bytes from the beginning of the tag to the desired data. If any of the offsets are zero, i.e. an indication that processing element is not present and the operation is not performed."