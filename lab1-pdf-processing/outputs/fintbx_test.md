# Financial Toolbox User's Guide
*Generated from fintbx.pdf (10 pages)*
---

<!-- Page: 1 -->
## Page 1
Financial Toolbox™

User's Guide

R2025b


**Figure:**
![Figure from page 1](figures/images/page_001_img_01.png)
---

<!-- Page: 2 -->
## Page 2
How to Contact MathWorks

Latest news:
www.mathworks.com

Sales and services:
www.mathworks.com/sales_and_services

User community:
www.mathworks.com/matlabcentral

Technical support:
www.mathworks.com/support/contact_us

Phone:
508-647-7000

The MathWorks, Inc.
1 Apple Hill Drive
Natick, MA 01760-2098

Financial Toolbox™ User's Guide

© COPYRIGHT 1995–2025 by The MathWorks, Inc.

The software described in this document is furnished under a license agreement. The software may be used or copied
only under the terms of the license agreement. No part of this manual may be photocopied or reproduced in any form
without prior written consent from The MathWorks, Inc.

FEDERAL ACQUISITION: This provision applies to all acquisitions of the Program and Documentation by, for, or through
the federal government of the United States. By accepting delivery of the Program or Documentation, the government
hereby agrees that this software or documentation qualifies as commercial computer software or commercial computer
software documentation as such terms are used or defined in FAR 12.212, DFARS Part 227.72, and DFARS 252.227-7014.
Accordingly, the terms and conditions of this Agreement and only those rights specified in this Agreement, shall pertain
to and govern the use, modification, reproduction, release, performance, display, and disclosure of the Program and
Documentation by the federal government (or other entity acquiring for or through the federal government) and shall
supersede any conflicting contractual terms or conditions. If this License fails to meet the government's needs or is
inconsistent in any respect with federal procurement law, the government agrees to return the Program and
Documentation, unused, to The MathWorks, Inc.

Trademarks

MATLAB and Simulink are registered trademarks of The MathWorks, Inc. See
www.mathworks.com/trademarks for a list of additional trademarks. Other product or brand names may be
trademarks or registered trademarks of their respective holders.

Patents

MathWorks products are protected by one or more U.S. patents. Please see www.mathworks.com/patents for
more information.


**Figure:**
![Figure from page 2](figures/images/page_002_img_01.png)

**Figure:**
![Figure from page 2](figures/images/page_002_img_02.png)

**Figure:**
![Figure from page 2](figures/images/page_002_img_03.png)
---

<!-- Page: 3 -->
## Page 3
Revision History

October 1995
First printing
January 1998
Second printing
Revised for Version 1.1
January 1999
Third printing
Revised for Version 2.0 (Release 11)
November 2000
Fourth printing
Revised for Version 2.1.2 (Release 12)
May 2003
Online only
Revised for Version 2.3 (Release 13)
June 2004
Online only
Revised for Version 2.4 (Release 14)
August 2004
Online only
Revised for Version 2.4.1 (Release 14+)
September 2005
Fifth printing
Revised for Version 2.5 (Release 14SP3)
March 2006
Online only
Revised for Version 3.0 (Release 2006a)
September 2006
Sixth printing
Revised for Version 3.1 (Release 2006b)
March 2007
Online only
Revised for Version 3.2 (Release 2007a)
September 2007
Online only
Revised for Version 3.3 (Release 2007b)
March 2008
Online only
Revised for Version 3.4 (Release 2008a)
October 2008
Online only
Revised for Version 3.5 (Release 2008b)
March 2009
Online only
Revised for Version 3.6 (Release 2009a)
September 2009
Online only
Revised for Version 3.7 (Release 2009b)
March 2010
Online only
Revised for Version 3.7.1 (Release 2010a)
September 2010
Online only
Revised for Version 3.8 (Release 2010b)
April 2011
Online only
Revised for Version 4.0 (Release 2011a)
September 2011
Online only
Revised for Version 4.1 (Release 2011b)
March 2012
Online only
Revised for Version 4.2 (Release 2012a)
September 2012
Online only
Revised for Version 5.0 (Release 2012b)
March 2013
Online only
Revised for Version 5.1 (Release 2013a)
September 2013
Online only
Revised for Version 5.2 (Release 2013b)
March 2014
Online only
Revised for Version 5.3 (Release 2014a)
October 2014
Online only
Revised for Version 5.4 (Release 2014b)
March 2015
Online only
Revised for Version 5.5 (Release 2015a)
September 2015
Online only
Revised for Version 5.6 (Release 2015b)
March 2016
Online only
Revised for Version 5.7 (Release 2016a)
September 2016
Online only
Revised for Version 5.8 (Release 2016b)
March 2017
Online only
Revised for Version 5.9 (Release 2017a)
September 2017
Online only
Revised for Version 5.10 (Release 2017b)
March 2018
Online only
Revised for Version 5.11 (Release 2018a)
September 2018
Online only
Revised for Version 5.12 (Release 2018b)
March 2019
Online only
Revised for Version 5.13 (Release 2019a)
September 2019
Online only
Revised for Version 5.14 (Release 2019b)
March 2020
Online only
Revised for Version 5.15 (Release 2020a)
September 2020
Online only
Revised for Version 6.0 (Release 2020b)
March 2021
Online only
Revised for Version 6.1 (Release 2021a)
September 2021
Online only
Revised for Version 6.2 (Release 2021b)
March 2022
Online only
Revised for Version 6.3 (Release 2022a)
September 2022
Online only
Revised for Version 6.4 (Release 2022b)
March 2023
Online only
Revised for Version 6.5 (Release 2023a)
September 2023
Online only
Revised for Version 23.2 (R2023b)
March 2024
Online only
Revised for Version 24.1 (R2024a)
September 2024
Online only
Revised for Version 24.2 (R2024b)
March 2025
Online only
Revised for Version 25.1 (R2025a)
September 2025
Online only
Rereleased for Version 25.2 (R2025b)

---

<!-- Page: 5 -->
## Page 5
Getting Started
1

Financial Toolbox Product Description . . . . . . . . . . . . . . . . . . . . . . . . . . . .
1-2

Expected Users . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
1-3

Analyze Sets of Numbers Using Matrix Functions . . . . . . . . . . . . . . . . . . .
1-4
Introduction . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
1-4
Key Definitions . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
1-4
Referencing Matrix Elements . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
1-4
Transposing Matrices . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
1-5

Matrix Algebra Refresher . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
1-7
Introduction . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
1-7
Adding and Subtracting Matrices . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
1-7
Multiplying Matrices . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
1-8
Dividing Matrices . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
1-11
Solving Simultaneous Linear Equations . . . . . . . . . . . . . . . . . . . . . . . . .
1-11
Operating Element by Element . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
1-13

Using Input and Output Arguments with Functions . . . . . . . . . . . . . . . . .
1-15
Input Arguments . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
1-15
Output Arguments . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
1-16

Performing Common Financial Tasks
2

Handle and Convert Dates . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
2-2
Date Formats . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
2-2
Date Conversions . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
2-3
Current Date and Time . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
2-7
Determining Specific Dates . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
2-8
Determining Holidays . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
2-8
Determining Cash-Flow Dates . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
2-9

Analyzing and Computing Cash Flows . . . . . . . . . . . . . . . . . . . . . . . . . . . .
2-11
Introduction . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
2-11
Interest Rates/Rates of Return . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
2-11
Present or Future Values . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
2-12
Depreciation . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
2-13
Annuities . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
2-13

v

Contents

---

<!-- Page: 6 -->
## Page 6
Pricing and Computing Yields for Fixed-Income Securities . . . . . . . . . .
2-15
Introduction . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
2-15
Fixed-Income Terminology . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
2-15
Framework . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
2-18
Default Parameter Values . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
2-18
Coupon Date Calculations . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
2-20
Yield Conventions . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
2-21
Pricing Functions . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
2-21
Yield Functions . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
2-21
Fixed-Income Sensitivities . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
2-22

Treasury Bills Defined . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
2-25

Computing Treasury Bill Price and Yield . . . . . . . . . . . . . . . . . . . . . . . . . .
2-26
Introduction . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
2-26
Treasury Bill Repurchase Agreements . . . . . . . . . . . . . . . . . . . . . . . . . .
2-26
Treasury Bill Yields . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
2-27

Term Structure of Interest Rates . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
2-29

Returns with Negative Prices . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
2-32
Negative Price Conversion . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
2-32
Analysis of Negative Price Returns . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
2-33
Visualization of Complex Returns . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
2-35
Conclusion . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
2-38

Pricing and Analyzing Equity Derivatives . . . . . . . . . . . . . . . . . . . . . . . . .
2-39
Introduction . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
2-39
Sensitivity Measures . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
2-39
Analysis Models . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
2-40

About Life Tables . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
2-44
Life Tables Theory . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
2-44

Case Study for Life Tables Analysis . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
2-46

Machine Learning for Statistical Arbitrage: Introduction . . . . . . . . . . . .
2-48

Machine Learning for Statistical Arbitrage I: Data Management and
Visualization . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
2-50

Machine Learning for Statistical Arbitrage II: Feature Engineering and
Model Development . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
2-59

Machine Learning for Statistical Arbitrage III: Training, Tuning, and
Prediction . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
2-69

Backtest Deep Learning Model for Algorithmic Trading of Limit Order
Book Data . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
2-78

vi
Contents

---

<!-- Page: 7 -->
## Page 7
Portfolio Analysis
3

Analyzing Portfolios . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
3-2

Portfolio Optimization Functions . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
3-3

Portfolio Construction Examples . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
3-5
Introduction . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
3-5
Efficient Frontier Example . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
3-5

Portfolio Selection and Risk Aversion . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
3-7
Introduction . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
3-7
Optimal Risky Portfolio . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
3-8

portopt Migration to Portfolio Object . . . . . . . . . . . . . . . . . . . . . . . . . . . .
3-11
Migrate portopt Without Output Arguments . . . . . . . . . . . . . . . . . . . . . .
3-11
Migrate portopt with Output Arguments . . . . . . . . . . . . . . . . . . . . . . . . .
3-12
Migrate portopt for Target Returns Within Range of Efficient Portfolio
Returns . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
3-13
Migrate portopt for Target Return Outside Range of Efficient Portfolio
Returns . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
3-14
Migrate portopt Using portcons Output for ConSet . . . . . . . . . . . . . . . . .
3-15
Integrate Output from portcons, pcalims, pcglims, and pcgcomp with a
Portfolio Object . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
3-17

Constraint Specification Using a Portfolio Object . . . . . . . . . . . . . . . . . .
3-19
Constraints for Efficient Frontier . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
3-19
Linear Constraint Equations . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
3-21
Specifying Group Constraints . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
3-24

Active Returns and Tracking Error Efficient Frontier . . . . . . . . . . . . . . .
3-27

Mean-Variance Portfolio Optimization Tools
4

Portfolio Optimization Theory . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
4-4
Portfolio Optimization Problems . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
4-4
Portfolio Problem Specification . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
4-4
Return Proxy . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
4-5
Risk Proxy . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
4-6

Supported Constraints for Portfolio Optimization Using Portfolio Objects
. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
4-9
Linear Inequality Constraints . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
4-9
Linear Equality Constraints . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
4-10
'Simple' Bound Constraints . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
4-10
'Conditional' Bound Constraints . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
4-11
Budget Constraints . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
4-11
Conditional Budget Constraints . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
4-12
Group Constraints . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
4-12

vii

---

<!-- Page: 8 -->
## Page 8
Group Ratio Constraints . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
4-13
Average Turnover Constraints . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
4-14
One-Way Turnover Constraints . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
4-14
Tracking Error Constraints . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
4-15
Cardinality Constraints . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
4-16

Default Portfolio Problem . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
4-17

Portfolio Object Workflow . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
4-18

Portfolio Object . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
4-20
Portfolio Object Properties and Functions . . . . . . . . . . . . . . . . . . . . . . . .
4-20
Working with Portfolio Objects . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
4-20
Setting and Getting Properties . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
4-20
Displaying Portfolio Objects . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
4-21
Saving and Loading Portfolio Objects . . . . . . . . . . . . . . . . . . . . . . . . . . .
4-21
Estimating Efficient Portfolios and Frontiers . . . . . . . . . . . . . . . . . . . . . .
4-21
Arrays of Portfolio Objects . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
4-22
Subclassing Portfolio Objects . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
4-23
Conventions for Representation of Data . . . . . . . . . . . . . . . . . . . . . . . . .
4-23

Creating the Portfolio Object . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
4-25
Syntax . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
4-25
Portfolio Problem Sufficiency . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
4-25
Portfolio Function Examples . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
4-26

Common Operations on the Portfolio Object . . . . . . . . . . . . . . . . . . . . . .
4-33
Naming a Portfolio Object . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
4-33
Configuring the Assets in the Asset Universe . . . . . . . . . . . . . . . . . . . . .
4-33
Setting Up a List of Asset Identifiers . . . . . . . . . . . . . . . . . . . . . . . . . . . .
4-33
Truncating and Padding Asset Lists . . . . . . . . . . . . . . . . . . . . . . . . . . . .
4-35

Setting Up an Initial or Current Portfolio . . . . . . . . . . . . . . . . . . . . . . . . .
4-37

Setting Up a Tracking Portfolio . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
4-40

Asset Returns and Moments of Asset Returns Using Portfolio Object . .
4-42
Assignment Using the Portfolio Function . . . . . . . . . . . . . . . . . . . . . . . .
4-42
Assignment Using the setAssetMoments Function . . . . . . . . . . . . . . . . .
4-43
Scalar Expansion of Arguments . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
4-44
Estimating Asset Moments from Prices or Returns . . . . . . . . . . . . . . . . .
4-45
Estimating Asset Moments with Missing Data . . . . . . . . . . . . . . . . . . . . .
4-47
Estimating Asset Moments from Time Series Data . . . . . . . . . . . . . . . . .
4-49

Working with a Riskless Asset . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
4-52

Working with Transaction Costs . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
4-54
Setting Transaction Costs Using the Portfolio Function . . . . . . . . . . . . . .
4-54
Setting Transaction Costs Using the setCosts Function . . . . . . . . . . . . . .
4-54
Setting Transaction Costs with Scalar Expansion . . . . . . . . . . . . . . . . . .
4-56

Working with Portfolio Constraints Using Defaults . . . . . . . . . . . . . . . . .
4-58
Setting Default Constraints for Portfolio Weights Using Portfolio Object
. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
4-58

viii
Contents


**Code Snippet (Page 8):**
```matlab
Creating the Portfolio Object . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
4-25
Syntax . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
4-25
Portfolio Problem Sufficiency . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
4-25
Portfolio Function Examples . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
4-26
```
---

<!-- Page: 9 -->
## Page 9
Working with 'Simple' Bound Constraints Using Portfolio Object . . . . .
4-62
Setting 'Simple' Bounds Using the Portfolio Function . . . . . . . . . . . . . . .
4-62
Setting 'Simple' Bounds Using the setBounds Function . . . . . . . . . . . . . .
4-62
Setting 'Simple' Bounds Using the Portfolio Function or setBounds Function
. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
4-63

Working with Budget Constraints Using Portfolio Object . . . . . . . . . . . .
4-65
Setting Budget Constraints Using the Portfolio Function . . . . . . . . . . . . .
4-65
Setting Budget Constraints Using the setBudget Function . . . . . . . . . . .
4-65

Working with Conditional Budget Constraints Using Portfolio Object . .
4-67
Setting Conditional Budget Constraints Using the Portfolio Function . . .
4-67
Setting Conditional Budget Constraints Using the setConditionalBudget
Function . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
4-67

Working with Group Constraints Using Portfolio Object . . . . . . . . . . . . .
4-69
Setting Group Constraints Using the Portfolio Function . . . . . . . . . . . . .
4-69
Setting Group Constraints Using the setGroups and addGroups Functions
. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
4-69

Working with Group Ratio Constraints Using Portfolio Object . . . . . . . .
4-72
Setting Group Ratio Constraints Using the Portfolio Function . . . . . . . . .
4-72
Setting Group Ratio Constraints Using the setGroupRatio and
addGroupRatio Functions . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
4-73

Working with Linear Equality Constraints Using Portfolio Object . . . . .
4-75
Setting Linear Equality Constraints Using the Portfolio Function . . . . . .
4-75
Setting Linear Equality Constraints Using the setEquality and addEquality
Functions . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
4-75

Working with Linear Inequality Constraints Using Portfolio Object . . . .
4-78
Setting Linear Inequality Constraints Using the Portfolio Function . . . . .
4-78
Setting Linear Inequality Constraints Using the setInequality and
addInequality Functions . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
4-78

Working with 'Conditional' BoundType, MinNumAssets, and
MaxNumAssets Constraints Using Portfolio Objects . . . . . . . . . . . . . .
4-81
Setting 'Conditional' BoundType Constraints Using the setBounds Function
. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
4-81
Setting the Limits on the Number of Assets Invested Using the
setMinMaxNumAssets Function . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
4-82

Working with Average Turnover Constraints Using Portfolio Object . . .
4-85
Setting Average Turnover Constraints Using the Portfolio Function . . . .
4-85
Setting Average Turnover Constraints Using the setTurnover Function . .
4-85

Working with One-Way Turnover Constraints Using Portfolio Object . . .
4-88
Setting One-Way Turnover Constraints Using the Portfolio Function . . . .
4-88
Setting Turnover Constraints Using the setOneWayTurnover Function . .
4-88

Working with Tracking Error Constraints Using Portfolio Object . . . . . .
4-91
Setting Tracking Error Constraints Using the Portfolio Function . . . . . . .
4-91
Setting Tracking Error Constraints Using the setTrackingError Function
. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
4-91

ix


**Code Snippet (Page 9):**
```matlab
Working with 'Simple' Bound Constraints Using Portfolio Object . . . . .
4-62
Setting 'Simple' Bounds Using the Portfolio Function . . . . . . . . . . . . . . .
4-62
Setting 'Simple' Bounds Using the setBounds Function . . . . . . . . . . . . . .
4-62
Setting 'Simple' Bounds Using the Portfolio Function or setBounds Function
. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
4-63
```
---

<!-- Page: 10 -->
## Page 10
Validate the Portfolio Problem for Portfolio Object . . . . . . . . . . . . . . . . .
4-94
Validating a Portfolio Set . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
4-94
Validating Portfolios . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
4-95

Estimate Efficient Portfolios for Entire Efficient Frontier for Portfolio
Object . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
4-98

Obtaining Portfolios Along the Entire Efficient Frontier . . . . . . . . . . . . .
4-99

Obtaining Endpoints of the Efficient Frontier . . . . . . . . . . . . . . . . . . . .
4-102

Obtaining Efficient Portfolios for Target Returns . . . . . . . . . . . . . . . . .
4-105

Obtaining Efficient Portfolios for Target Risks . . . . . . . . . . . . . . . . . . . .
4-108

Efficient Portfolio That Maximizes Sharpe Ratio . . . . . . . . . . . . . . . . . .
4-111

Choosing and Controlling the Solver for Mean-Variance Portfolio
Optimization . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
4-114
Using 'lcprog' and 'quadprog' . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
4-114
Using the Mixed Integer Nonlinear Programming (MINLP) Solver . . . .
4-115
Solver Guidelines for Portfolio Objects . . . . . . . . . . . . . . . . . . . . . . . . .
4-115
Solver Guidelines for Custom Objective Problems Using Portfolio Objects
. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
4-119

Estimate Efficient Frontiers for Portfolio Object . . . . . . . . . . . . . . . . . .
4-122
Obtaining Portfolio Risks and Returns . . . . . . . . . . . . . . . . . . . . . . . . . .
4-122

Plotting the Efficient Frontier for a Portfolio Object . . . . . . . . . . . . . . .
4-125

Postprocessing Results to Set Up Tradable Portfolios . . . . . . . . . . . . . .
4-130

When to Use Portfolio Objects Over Optimization Toolbox . . . . . . . . . .
4-132
Always Use Portfolio, PortfolioCVaR, or PortfolioMAD Object . . . . . . . .
4-134
Preferred Use of Portfolio, PortfolioCVaR, or PortfolioMAD Object . . . .
4-135
Use Optimization Toolbox . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
4-136

Comparison of Methods for Covariance Estimation . . . . . . . . . . . . . . . .
4-138

Choose MINLP Solvers for Portfolio Problems . . . . . . . . . . . . . . . . . . . .
4-140

Troubleshooting Portfolio Optimization Results . . . . . . . . . . . . . . . . . .
4-145
Portfolio Object Destroyed When Modifying . . . . . . . . . . . . . . . . . . . . .
4-145
Optimization Fails with “Bad Pivot” Message . . . . . . . . . . . . . . . . . . . .
4-145
Speed of Optimization . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
4-145
Matrix Incompatibility and "Non-Conformable" Errors . . . . . . . . . . . . .
4-145
Missing Data Estimation Fails . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
4-145
mv_optim_transform Errors . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
4-145
solveContinuousCustomObjProb or solveMICustomObjProb Errors . . . .
4-146
Efficient Portfolios Do Not Make Sense . . . . . . . . . . . . . . . . . . . . . . . . .
4-146
Efficient Frontiers Do Not Make Sense . . . . . . . . . . . . . . . . . . . . . . . . .
4-146
Troubleshooting estimateCustomObjectivePortfolio . . . . . . . . . . . . . . .
4-148
Troubleshooting for Setting 'Conditional' BoundType, MinNumAssets, and
MaxNumAssets Constraints . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
4-148

x
Contents

---
