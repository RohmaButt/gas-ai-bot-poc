/*
====================================================================================================
 SCRIPT TO INSERT COMPREHENSIVE DUMMY DATA INTO THE 'Gas' DATABASE
====================================================================================================
 Goal:        Insert a minimum of 5 records into every table.
 Strategy:
 1. TRUNCATE ALL TABLES to ensure a clean slate.
 2. DISABLE ALL TRIGGERS to allow for bulk data insertion.
 3. Insert FOUNDATIONAL DATA (Companies, Employees, Vendors, Products, Customers).
 4. Create TRANSACTIONAL DATA that tells a story (Sales, Deliveries, Payments, Inventory).
 5. Populate all SUPPORTING and MISCELLANEOUS tables with plausible data.
 6. RE-ENABLE ALL TRIGGERS once data insertion is complete.
====================================================================================================
*/

USE [Gas]
GO

-- =================================================================
-- Step 0: Truncate All Tables to Avoid Primary Key Conflicts
-- =================================================================
PRINT 'Step 0: Truncating all tables to ensure a clean slate...';
EXEC sp_msforeachtable 'TRUNCATE TABLE ?';
GO

-- =================================================================
-- Step 1: Disable All Triggers
-- =================================================================
PRINT 'Step 1: Disabling all triggers in the database...';
EXEC sp_msforeachtable "ALTER TABLE ? DISABLE TRIGGER all";
GO

-- =================================================================
-- Step 2: Foundational & Core Entity Data
-- =================================================================
PRINT 'Step 2: Inserting foundational data (Companies, Employees, Vendors, etc.)...';

-- BCOMPANY (Company Info)
-- Note: Assumed COMPNAME, COMPSNAME are VARCHAR(50), UNIFYNO is VARCHAR(20), IP1, IP2 are VARCHAR(15)
INSERT INTO [dbo].[BCOMPANY] ([COMPNO], [COMPNAME], [COMPSNAME], [UNIFYNO], [ISOBJNO], [IP1], [IP2]) VALUES
('C001', 'Global Gas', 'GGS', '12345678', 'Y', '192.168.1.10', '192.168.1.11'),
('C002', 'Regional Propane', 'RP-LLC', '87654321', 'Y', '192.168.2.10', '192.168.2.11'),
('C003', 'City Gasworks', 'CGW', '11223344', 'N', '10.0.0.5', '10.0.0.6'),
('C004', 'Suburban Fuel', 'SFuel', '55667788', 'N', '10.10.0.5', '10.10.0.6'),
('C005', 'Industrial Gases', 'IGC', '99887766', 'N', '172.16.0.5', '172.16.0.6');

-- BBranch (Company Branches)
INSERT INTO [dbo].[BBranch] ([COMPNO], [COMP], [COMPNAME], [COMPSNAME], [UNIFYNO]) VALUES
('C001', 'BR01', 'GGS North', 'GGS-N', '12345678'),
('C001', 'BR02', 'GGS South', 'GGS-S', '12345679'),
('C002', 'BR03', 'RP-LLC East', 'RP-E', '87654321'),
('C002', 'BR04', 'RP-LLC West', 'RP-W', '87654322'),
('C003', 'BR05', 'CGW HQ', 'CGW-HQ', '11223344');

-- ABDEPT & BDEPART (Departments)
INSERT INTO [dbo].[ABDEPT] ([COMPNO], [DPID], [DPNAME]) VALUES
('C001', 'SALE', 'Sales'), ('C001', 'LOGI', 'Logistics'), ('C001', 'FINA', 'Finance'), ('C001', 'ADMN', 'Admin'), ('C001', 'HR', 'HR');
INSERT INTO [dbo].[BDEPART] ([COMPNO], [DPID], [FNAME], [SNAME], [DEFWNO]) VALUES
('C001', 'SALE', 'Sales Dept', 'Sales', 'W01'), ('C001', 'LOGI', 'Logistics', 'Logistics', 'W01'),
('C001', 'FINA', 'Finance', 'Finance', 'W01'), ('C001', 'ADMN', 'Administration', 'Admin', 'W01'),
('C002', 'SALE', 'Sales Team', 'Sales', 'W02');

-- EMPLOYEE
-- Note: Assumed CNAME is VARCHAR(50), JOB is VARCHAR(10), SEX is CHAR(1)
INSERT INTO [dbo].[EMPLOYEE] ([COMPNO], [EMPNO], [CNAME], [DPID], [JOB], [SEX], [SDATE]) VALUES
('C001', 'E001', 'John Doe', 'LOGI', 'DR', 'M', '2020-01-15'), 
('C001', 'E002', 'Jane Smith', 'SALE', 'SA', 'F', '2021-03-10'),
('C001', 'E003', 'Peter Jones', 'LOGI', 'DR', 'M', '2019-11-05'), 
('C001', 'E004', 'Mary Williams', 'FINA', 'AC', 'F', '2022-02-20'),
('C001', 'E005', 'David Brown', 'ADMN', 'MG', 'M', '2018-06-01');

-- SYSUSER (System Login Accounts)
-- Note: Assumed ID, PASSWORD, CNAME are VARCHAR(50), USERKIND is VARCHAR(1)
INSERT INTO [dbo].[SYSUSER] ([COMPNO], [EMP_ID], [ID], [PASSWORD], [CNAME], [USERKIND], [COMP]) VALUES
('C001', 'E001', 'johnd', 'pass123', 'John Doe', '2', 'BR01'), 
('C001', 'E002', 'janes', 'pass123', 'Jane Smith', '1', 'BR01'),
('C001', 'E003', 'peterj', 'pass123', 'Peter Jones', '2', 'BR02'), 
('C001', 'E004', 'maryw', 'pass123', 'Mary Williams', '1', 'BR01'),
('C001', 'E005', 'davidb', 'pass123', 'David Brown', '0', 'BR01');

-- BVENDOR (Suppliers)
-- Note: Assumed FNAME, SNAME are VARCHAR(50), VTYPE, YNCARSEQ are VARCHAR(1)
INSERT INTO [dbo].[BVENDOR] ([COMPNO], [VENO], [FNAME], [SNAME], [VTYPE], [YNCARSEQ]) VALUES
('C001', 'V-GAS1', 'Primary Gas Supply', 'GasMain', '1', 'Y'), 
('C001', 'V-CYL1', 'Cylinder Mfg', 'Cylinders', '1', 'N'),
('C001', 'V-APL1', 'Appliance World', 'ApplianceW', '2', 'N'), 
('C001', 'V-OFF1', 'Office Supply', 'OfficeSup', '2', 'N'),
('C001', 'V-MNT1', 'Vehicle Maint', 'CarSvc', '2', 'N');

-- BWAHOUSE (Warehouses)
INSERT INTO [dbo].[BWAHOUSE] ([COMPNO], [WNO], [WNAME], [WSNAME]) VALUES
('C001', 'W01', 'Main Warehouse', 'Main WH'), 
('C001', 'W02', 'North Dist', 'North WH'),
('C001', 'W03', 'South Storage', 'South WH'), 
('C002', 'W04', 'Propane Depot', 'Main Depot'),
('C002', 'W05', 'Secondary Depot', 'Second Depot');

-- KEYN (Key-Name lookup table)
INSERT INTO [dbo].[KEYN] ([KCDE_1], [KCDE_2], [KCNT], [KNOTE2]) VALUES
('CTYPE', 'A', 'Residential', 'Standard Home'), 
('CTYPE', 'B', 'Commercial', 'Restaurant/Biz'),
('CTYPE', 'C', 'Industrial', 'Factory'), 
('GTYPE', '1', 'Regular Delivery', 'Standard'),
('GTYPE', '2', 'Cylinder Deposit', 'New Customer');

-- PARAMS (System Parameters)
-- Note: Assumed ENAME, CNAME, PARAM are VARCHAR(50)
INSERT INTO [dbo].[PARAMS] ([SUBJ], [SEQ], [ENAME], [CNAME], [PARAM]) VALUES
('SYS', 1, 'YNAbnormal', 'Abnormal Check', 'Y'), 
('SYS', 2, 'GasWeight', 'Cylinder Weights', '50,20,18,16,10,4'),
('SYS', 3, 'DefaultTax', 'Tax Rate', '0.05'), 
('SYS', 4, 'SysDpid', 'Default DPID', 'ADMN'),
('SYS', 5, 'AutoAssign', 'Auto-Assign Driver', 'Y');

GO

-- =================================================================
-- Step 3: Asset, Product, and Inventory Data
-- =================================================================
PRINT 'Step 3: Inserting asset, product, and inventory data...';

-- BGasSpec (Individual Gas Cylinders)
-- Note: Assumed BARCODE, GSPEC, LASTNO, VENO are VARCHAR(20), GSTATE is VARCHAR(1)
INSERT INTO [dbo].[BGasSpec] ([COMPNO], [GSERNO], [BARCODE], [BEDATE], [CHKDATE], [NXCHDATE], [GSPEC], [GWEIGHT], [GSTATE], [LASTNO], [LASTDATE], [VENO]) VALUES
('C001', 'CYL-001', 'BC-001', '2020-01-01', '2025-01-01', '2030-01-01', '20', 21.5, '1', 'V-GAS1', GETDATE()-1, 'V-CYL1'),
('C001', 'CYL-002', 'BC-002', '2020-02-01', '2025-02-01', '2030-02-01', '20', 21.6, '1', 'V-GAS1', GETDATE()-1, 'V-CYL1'),
('C001', 'CYL-003', 'BC-003', '2021-03-01', '2026-03-01', '2031-03-01', '50', 52.0, '1', 'V-GAS1', GETDATE()-1, 'V-CYL1'),
('C001', 'CYL-004', 'BC-004', '2021-04-01', '2026-04-01', '2031-04-01', '50', 51.9, '0', 'E001', GETDATE()-2, 'V-CYL1'),
('C001', 'CYL-005', 'BC-005', '2022-05-01', '2027-05-01', '2032-05-01', '16', 17.5, '0', '1001', GETDATE()-30, 'V-CYL1');

-- BPRODUCT (Non-Gas Products)
-- Note: Assumed PNAME is VARCHAR(50), UNIT is VARCHAR(10)
INSERT INTO [dbo].[BPRODUCT] ([COMPNO], [PNO], [PNAME], [UNIT], [COST], [PRICE], [ISQTY], [VENO]) VALUES
('C001', 'PROD-STOVE-01', '2-Burner Stove', 'EA', 3500, 4999, 'Y', 'V-APL1'),
('C001', 'PROD-REG-01', 'Safety Regulator', 'EA', 300, 550, 'Y', 'V-APL1'),
('C001', 'PROD-HOSE-01', '2m Gas Hose', 'EA', 150, 250, 'Y', 'V-APL1'),
('C001', 'SVC-INSPECT-01', 'Safety Inspection', 'SVC', 200, 500, 'N', 'V-APL1'),
('C001', 'PROD-LIGHTER-01', 'Gas Lighter', 'EA', 50, 100, 'Y', 'V-APL1');

-- BPRODQTY (Inventory Stock for Products)
INSERT INTO [dbo].[BPRODQTY] ([COMPNO], [PNO], [WNO], [GQTY], [LADATE]) VALUES
('C001', 'PROD-STOVE-01', 'W01', 10, GETDATE()-20), 
('C001', 'PROD-STOVE-01', 'W02', 5, GETDATE()-20),
('C001', 'PROD-REG-01', 'W01', 50, GETDATE()-20), 
('C001', 'PROD-HOSE-01', 'W01', 100, GETDATE()-20),
('C001', 'PROD-LIGHTER-01', 'W01', 200, GETDATE()-20);

-- BCarData (Company Vehicles)
-- Note: Assumed CLICENSE is VARCHAR(20), FUEL is VARCHAR(10)
INSERT INTO [dbo].[BCarData] ([COMPNO], [CARNO], [CLICENSE], [CYEAR], [EMPNO], [FUEL], [DPID]) VALUES
('C001', 'CAR1', 'ABC-1111', '2020', 'E001', 'Gas', 'LOGI'), 
('C001', 'CAR2', 'DEF-2222', '2021', 'E003', 'Gas', 'LOGI'),
('C001', 'CAR3', 'GHI-3333', '2019', NULL, 'Diesel', 'LOGI'), 
('C001', 'CAR4', 'JKL-4444', '2022', NULL, 'Gas', 'LOGI'),
('C001', 'CAR5', 'MNO-5555', '2018', NULL, 'Diesel', 'LOGI');

GO

-- =================================================================
-- Step 4: Customer Data
-- =================================================================
PRINT 'Step 4: Inserting customer data...';

-- BCUSTOM (Customer Information)
-- Note: Assumed FNAME, SNAME, TEL1, CITY, AREA, ROAD, ADDRESSA are VARCHAR(50), YNFMETER is CHAR(1)
INSERT INTO [dbo].[BCUSTOM] ([COMPNO], [CUSTNO], [FNAME], [SNAME], [TEL1], [CITY], [AREA], [ROAD], [ADDRESSA], [YNFMETER], [DATECREATE], [DATELAST], [PD], [MM1], [MM2], [MM3], [MM4], [MM5], [COMP]) VALUES
('C001', 1001, 'Alice Johnson', 'Alice', '0912345678', 'Taipei', 'Daan', 'Fuxing Rd', 'Taipei, Daan, Fuxing Rd #1', 'N', '2022-05-20', GETDATE()-30, 30, 750, 650, 550, 0, 0, 'BR01'),
('C001', 1002, 'Bobs Burgers', 'Bob', '0227771234', 'Taipei', 'Xinyi', 'City Hall Rd', 'Taipei, Xinyi, City Hall #2', 'Y', '2021-01-15', GETDATE()-15, 14, 720, 620, 520, 420, 0, 'BR01'),
('C001', 1003, 'Charlie Dental', 'Charlie', '0988765432', 'New Taipei', 'Banciao', 'Wenhua Rd', 'New Taipei, Banciao, Wenhua #3', 'N', '2023-08-01', GETDATE()-45, 45, 750, 650, 0, 0, 0, 'BR02'),
('C001', 1004, 'Diana Prints', 'Diana', '033338888', 'Taoyuan', 'Taoyuan', 'Zhongzheng Rd', 'Taoyuan, Zhongzheng Rd #4', 'N', '2020-02-10', GETDATE()-60, 60, 740, 640, 0, 0, 0, 'BR02'),
('C001', 1005, 'Eva Flowers', 'Eva', '0911222333', 'Taipei', 'Zhongshan', 'Nanjing Rd', 'Taipei, Zhongshan, Nanjing #5', 'N', '2023-11-20', GETDATE()-25, 25, 750, 650, 550, 0, 0, 'BR01');

GO

-- =================================================================
-- Step 5: Transactional Data (Deliveries, Sales, Financials)
-- =================================================================
PRINT 'Step 5: Inserting transactional data...';

-- Story 1: A recent gas delivery for Customer 1001
INSERT INTO [dbo].[DWORK] ([COMPNO], [CALLNO], [NEWDATE], [SADATE], [CUSTNO], [FNAME], [NOTE8], [GTYPE], [CC2], [BB2], [WHONO], [WHONONAME], [EMPACC], [DPID], [ASSIGNEMP], [ASSIGNDATE], [NEWEMP], [CARRYDATE])
VALUES ('C001', 'W250720001', GETDATE()-3, GETDATE()-3, 1001, 'Alice Johnson', 'Req 20kg gas', '1', 1, 1, 'E001', 'John Doe', 'E002', 'LOGI', 'E002', GETDATE()-3, 'E002', GETDATE()-3);
INSERT INTO [dbo].[DGDailyCar] ([COMPNO], [IONO], [GIODATE], [GIOTIME], [VENO], [EMPNO], [EMPNAME], [CARSEQ])
VALUES ('C001', 'T250720001', GETDATE()-3, '09:30:00', 'V-GAS1', 'E001', 'John Doe', 1);
INSERT INTO [dbo].[DGDailyCarD] ([COMPNO], [IONO], [BARCODE], [G01], [LASTNO], [YNINI], [SANO], [GSERNO], [GSPEC], [LADATE], [RETDATE])
VALUES ('C001', 'T250720001', 'BC-001', '1', '1001', 'Y', 'W250720001', 'CYL-001', '20', GETDATE()-3, NULL);
INSERT INTO [dbo].[DSAGAS] ([COMPNO], [SANO], [SADATE], [CUSTNO], [AMOUNT], [PAYED], [COST], [EMPNO], [EMPNAME], [GTYPE], [CC2], [BB2], [TKG])
VALUES ('C001', 'W250720001', GETDATE()-3, 1001, 650, 650, 450, 'E001', 'John Doe', '1', 1, 1, 20);
INSERT INTO [dbo].[GCUSBALM] ([COMPNO], [CBNO], [CBDATE], [CUSTNO], [AMOUNT], [BCASH]) VALUES ('C001', 'P250720001', GETDATE()-3, 1001, 650, 650);
INSERT INTO [dbo].[GCUSBALD] ([COMPNO], [CBNO], [SEQ], [SANO], [SKIND], [NOAMOUNT], [NOWGO]) VALUES ('C001', 'P250720001', 1, 'W250720001', 'G', 650, 650);

-- Story 2: Sale of a Gas Stove to Customer 1002
INSERT INTO [dbo].[DSAMASTER] ([COMPNO], [SANO], [SADATE], [CUSTNO], [FNAME], [AMOUNT], [PAYED], [EMPNO], [EMPNAME], [WNO], [DPID])
VALUES ('C001', 'S250721001', GETDATE()-2, 1002, 'Bobs Burgers', 4999, 0, 'E002', 'Jane Smith', 'W01', 'SALE');
INSERT INTO [dbo].[DSADETAIL] ([COMPNO], [SANO], [SEQ], [PNO], [PNAME], [QTY], [PRICE], [TOTAL], [COST], [WNO])
VALUES ('C001', 'S250721001', 1, 'PROD-STOVE-01', '2-Burner Stove', 1, 4999, 4999, 3500, 'W01');

-- Add 4 more misc sales records
INSERT INTO [dbo].[DSAMASTER] ([COMPNO], [SANO], [SADATE], [CUSTNO], [FNAME], [AMOUNT], [PAYED], [EMPNO], [EMPNAME], [WNO], [DPID]) VALUES
('C001', 'S250721002', GETDATE()-2, 1003, 'Charlie Dental', 550, 550, 'E002', 'Jane Smith', 'W01', 'SALE'),
('C001', 'S250722001', GETDATE()-1, 1004, 'Diana Prints', 250, 250, 'E002', 'Jane Smith', 'W01', 'SALE'),
('C001', 'S250722002', GETDATE()-1, 1005, 'Eva Flowers', 100, 0, 'E002', 'Jane Smith', 'W01', 'SALE'),
('C001', 'S250723001', GETDATE(), 1001, 'Alice Johnson', 550, 550, 'E002', 'Jane Smith', 'W01', 'SALE');
INSERT INTO [dbo].[DSADETAIL] ([COMPNO], [SANO], [SEQ], [PNO], [PNAME], [QTY], [PRICE], [TOTAL], [COST], [WNO]) VALUES
('C001', 'S250721002', 1, 'PROD-REG-01', 'Safety Regulator', 1, 550, 550, 300, 'W01'),
('C001', 'S250722001', 1, 'PROD-HOSE-01', '2m Gas Hose', 1, 250, 250, 150, 'W01'),
('C001', 'S250722002', 1, 'PROD-LIGHTER-01', 'Gas Lighter', 1, 100, 100, 50, 'W01'),
('C001', 'S250723001', 1, 'PROD-REG-01', 'Safety Regulator', 1, 550, 550, 300, 'W01');

-- Story 3: Inventory Purchase from Vendor
INSERT INTO [dbo].[DINMASTER] ([COMPNO], [INNO], [INDATE], [VENO], [AMOUNT], [PAYED], [WNO], [DPID])
VALUES ('C001', 'P250715001', GETDATE()-8, 'V-APL1', 38000, 0, 'W01', 'LOGI');
INSERT INTO [dbo].[DINDETAIL] ([COMPNO], [INNO], [SEQ], [PNO], [QTY], [PRICE], [AMOUNT], [WNO]) VALUES
('C001', 'P250715001', 1, 'PROD-STOVE-01', 10, 3500, 35000, 'W01'),
('C001', 'P250715001', 2, 'PROD-REG-01', 10, 300, 3000, 'W01');

-- Add 4 more misc purchase records
INSERT INTO [dbo].[DINMASTER] ([COMPNO], [INNO], [INDATE], [VENO], [AMOUNT], [PAYED], [WNO], [DPID]) VALUES
('C001', 'P250716001', GETDATE()-7, 'V-APL1', 15000, 15000, 'W01', 'LOGI'),
('C001', 'P250717001', GETDATE()-6, 'V-OFF1', 5000, 5000, 'W01', 'ADMN'),
('C001', 'P250718001', GETDATE()-5, 'V-MNT1', 8000, 0, 'W01', 'LOGI'),
('C001', 'P250719001', GETDATE()-4, 'V-GAS1', 100000, 0, 'W01', 'LOGI');
INSERT INTO [dbo].[DINDETAIL] ([COMPNO], [INNO], [SEQ], [PNO], [QTY], [PRICE], [AMOUNT], [WNO]) VALUES
('C001', 'P250716001', 1, 'PROD-HOSE-01', 100, 150, 15000, 'W01'),
('C001', 'P250717001', 1, 'PROD-LIGHTER-01', 100, 50, 5000, 'W01'),
('C001', 'P250718001', 1, 'SVC-INSPECT-01', 1, 8000, 8000, 'W01'),
('C001', 'P250719001', 1, 'SVC-INSPECT-01', 1, 100000, 100000, 'W01');

-- Story 4: Paying a Vendor
INSERT INTO [dbo].[GVENBALM] ([COMPNO], [VBNO], [VBDATE], [VENO], [AMOUNT], [BCASH])
VALUES ('C001', 'PV25072201', GETDATE()-1, 'V-APL1', 15000, 15000);
INSERT INTO [dbo].[GVENBALD] ([COMPNO], [VBNO], [SEQ], [BUNO], [BKIND], [NOAMOUNT], [NOWGO])
VALUES ('C001', 'PV25072201', 1, 'P250716001', 'K', 15000, 15000);
-- Add 4 more payments
INSERT INTO [dbo].[GVENBALM] ([COMPNO], [VBNO], [VBDATE], [VENO], [AMOUNT], [BCASH]) VALUES
('C001', 'PV25072202', GETDATE()-1, 'V-OFF1', 5000, 5000), 
('C001', 'PV25072203', GETDATE()-1, 'V-MNT1', 4000, 4000),
('C001', 'PV25072301', GETDATE(), 'V-GAS1', 50000, 50000), 
('C001', 'PV25072302', GETDATE(), 'V-APL1', 10000, 10000);
INSERT INTO [dbo].[GVENBALD] ([COMPNO], [VBNO], [SEQ], [BUNO], [BKIND], [NOAMOUNT], [NOWGO]) VALUES
('C001', 'PV25072202', 1, 'P250717001', 'K', 5000, 5000), 
('C001', 'PV25072203', 1, 'P250718001', 'K', 8000, 4000),
('C001', 'PV25072301', 1, 'P250719001', 'K', 100000, 50000), 
('C001', 'PV25072302', 1, 'P250715001', 'K', 38000, 10000);
GO

-- =================================================================
-- Step 6: Populate All Remaining Miscellaneous Tables
-- =================================================================
PRINT 'Step 6: Populating all remaining miscellaneous tables...';

-- Financial / Accounting Tables
INSERT INTO [dbo].[ABSUBJ] ([COMPNO], [OBJNO], [NAME], [DC]) VALUES
('C001', '1101', 'Cash', 'D'), ('C001', '1102', 'Accounts Receivable', 'D'), 
('C001', '2101', 'Accounts Payable', 'C'), ('C001', '4101', 'Sales Revenue', 'C'), 
('C001', '5101', 'Cost of Goods Sold', 'D');
INSERT INTO [dbo].[ADMASTER] ([COMPNO], [ACCNO], [ACCDATE], [ACCTYPE], [DPID], [TDAMOUNT], [TCAMOUNT]) VALUES
('C001', 'J250701001', GETDATE()-22, '1', 'FINA', 5000, 5000), 
('C001', 'J250702001', GETDATE()-21, '1', 'FINA', 1200, 1200),
('C001', 'J250703001', GETDATE()-20, '1', 'FINA', 800, 800), 
('C001', 'J250704001', GETDATE()-19, '1', 'FINA', 3500, 3500),
('C001', 'J250705001', GETDATE()-18, '1', 'FINA', 2400, 2400);
INSERT INTO [dbo].[ADDETAIL] ([COMPNO], [ACCNO], [SEQ], [ACCDATE], [DC], [OBJNO], [ACCDESC], [AMOUNT]) VALUES
('C001', 'J250701001', 1, GETDATE()-22, 'D', '1101', 'Cash deposit', 5000), 
('C001', 'J250701001', 2, GETDATE()-22, 'C', '1102', 'Customer payment', 5000),
('C001', 'J250702001', 1, GETDATE()-21, 'D', '5101', 'COGS for sale', 1200), 
('C001', 'J250702001', 2, GETDATE()-21, 'C', '4101', 'Revenue from sale', 1200),
('C001', 'J250703001', 1, GETDATE()-20, 'D', '2101', 'Paid vendor', 800);

-- Inventory Transfer & Stocktake
INSERT INTO [dbo].[DTransM] ([COMPNO], [TRNO], [TRDATE], [WNOS], [WNOD], [EMPNO]) VALUES
('C001', 'TR25070101', GETDATE()-20, 'W01', 'W02', 'E005'), 
('C001', 'TR25070201', GETDATE()-19, 'W01', 'W03', 'E005'),
('C001', 'TR25070301', GETDATE()-18, 'W02', 'W01', 'E005'), 
('C001', 'TR25070401', GETDATE()-17, 'W03', 'W01', 'E005'),
('C001', 'TR25070501', GETDATE()-16, 'W01', 'W02', 'E005');
INSERT INTO [dbo].[DTransD] ([COMPNO], [TRNO], [SEQ], [PNO], [QTYR]) VALUES
('C001', 'TR25070101', 1, 'PROD-STOVE-01', 2), 
('C001', 'TR25070201', 1, 'PROD-REG-01', 10),
('C001', 'TR25070301', 1, 'PROD-HOSE-01', 20), 
('C001', 'TR25070401', 1, 'PROD-LIGHTER-01', 50),
('C001', 'TR25070501', 1, 'PROD-STOVE-01', 1);
INSERT INTO [dbo].[FTAKESTOCKM] ([COMPNO], [PDNO], [PDDATE], [WNO], [PDEMPNO]) VALUES
('C001', 'ST25060101', GETDATE()-50, 'W01', 'E004'), 
('C001', 'ST25060102', GETDATE()-50, 'W02', 'E004'),
('C001', 'ST25060103', GETDATE()-49, 'W01', 'E004'), 
('C001', 'ST25060104', GETDATE()-49, 'W02', 'E004'),
('C001', 'ST25060105', GETDATE()-48, 'W03', 'E004');
INSERT INTO [dbo].[FTAKESTOCKD] ([COMPNO], [PDNO], [SEQ], [PNO], [INIQTY], [PDQTY], [CHQTY]) VALUES
('C001', 'ST25060101', 1, 'PROD-STOVE-01', 12, 12, 0), 
('C001', 'ST25060101', 2, 'PROD-REG-01', 50, 49, -1),
('C001', 'ST25060102', 1, 'PROD-HOSE-01', 100, 100, 0), 
('C001', 'ST25060102', 2, 'PROD-LIGHTER-01', 200, 200, 0),
('C001', 'ST25060103', 1, 'PROD-STOVE-01', 11, 11, 0);

-- System Security Tables
INSERT INTO [dbo].[SECFORM] ([FORM], [CAPTION], [PARENT], [SEQ], [VISIBLE]) VALUES
('FRM_CUST', 'Customer Mgmt', 'MAIN_MENU', 1, 'Y'), 
('FRM_SALE', 'Sales Order', 'MAIN_MENU', 2, 'Y'),
('FRM_INVT', 'Inventory', 'MAIN_MENU', 3, 'Y'), 
('FRM_REPO', 'Reports', 'MAIN_MENU', 4, 'Y'),
('FRM_SYST', 'System Settings', 'MAIN_MENU', 5, 'Y');
INSERT INTO [dbo].[RLIST] ([COMPNO], [EMP_ID], [FORM], [SEC_Q], [SEC_I], [SEC_E], [SEC_D]) VALUES
('C001', 'E002', 'FRM_CUST', 'Y', 'Y', 'Y', 'N'), 
('C001', 'E002', 'FRM_SALE', 'Y', 'Y', 'Y', 'Y'),
('C001', 'E005', 'FRM_CUST', 'Y', 'Y', 'Y', 'Y'), 
('C001', 'E005', 'FRM_SALE', 'Y', 'Y', 'Y', 'Y'),
('C001', 'E005', 'FRM_SYST', 'Y', 'Y', 'Y', 'Y');

-- Logging and Miscellaneous Tables
INSERT INTO [dbo].[FTEL] ([TDATE], [TEL], [CUSTNO], [EMPNO], [COMPNO]) VALUES
(GETDATE()-1, '0912345678', 1001, 'E002', 'C001'), 
(GETDATE()-1, '0227771234', 1002, 'E002', 'C001'),
(GETDATE(), '0988765432', 1003, 'E002', 'C001'), 
(GETDATE(), '033338888', 1004, 'E002', 'C001'),
(GETDATE(), '0911222333', 1005, 'E002', 'C001');
INSERT INTO [dbo].[FLOGIN] ([EMPNO], [CNAME], [LOGINTIME], [INTIME], [EXITTIME], [COMPNO]) VALUES
('E002', 'Jane Smith', '20250722090000', GETDATE()-1, GETDATE()-1, 'C001'), 
('E001', 'John Doe', '20250722083000', GETDATE()-1, GETDATE()-1, 'C001'),
('E005', 'David Brown', '20250722090500', GETDATE()-1, NULL, 'C001'), 
('E002', 'Jane Smith', '20250723090100', GETDATE(), NULL, 'C001'),
('E003', 'Peter Jones', '20250723083500', GETDATE(), NULL, 'C001');
INSERT INTO [dbo].[DailyArea] ([COMPNO], [GDATE], [ARNO], [SDATE], [EMPNO]) VALUES
('C001', GETDATE(), 'N', GETDATE(), 'E001'), 
('C001', GETDATE(), 'S', GETDATE(), 'E003'),
('C001', GETDATE()-1, 'N', GETDATE()-1, 'E001'), 
('C001', GETDATE()-1, 'S', GETDATE()-1, 'E003'),
('C001', GETDATE()-2, 'N', GETDATE()-2, 'E001');

-- Address Lookup tables
-- Note: Added non-null values for ecityarea, tcityarea, hcityarea, pcityarea, eroad
INSERT INTO [dbo].[area] ([zipcode], [city], [area], [ecityarea], [tcityarea], [hcityarea], [pcityarea]) VALUES 
('106', 'Taipei', 'Daan', 'Daan', 'Daan', 'Daan', 'Daan'), 
('110', 'Taipei', 'Xinyi', 'Xinyi', 'Xinyi', 'Xinyi', 'Xinyi'), 
('104', 'Taipei', 'Zhongshan', 'Zhongshan', 'Zhongshan', 'Zhongshan', 'Zhongshan'), 
('220', 'New Taipei', 'Banciao', 'Banciao', 'Banciao', 'Banciao', 'Banciao'), 
('330', 'Taoyuan', 'Taoyuan', 'Taoyuan', 'Taoyuan', 'Taoyuan', 'Taoyuan');
INSERT INTO [dbo].[road1] ([zipcode], [road], [road_no], [city], [area], [rkey], [road1], [roada], [phon], [zip3a], [uword], [eroad]) VALUES
('106', 'Fuxing S. Rd', '2', 'Taipei', 'Daan', 'R1', 'F', 'S', '02', '106', 'U1', 'Fuxing'),
('110', 'City Hall Rd', '1', 'Taipei', 'Xinyi', 'R2', 'C', 'H', '02', '110', 'U2', 'City Hall'),
('104', 'Nanjing E. Rd', '1', 'Taipei', 'Zhongshan', 'R3', 'N', 'E', '02', '104', 'U3', 'Nanjing'),
('220', 'Wenhua Rd', '1', 'New Taipei', 'Banciao', 'R4', 'W', 'R', '02', '220', 'U4', 'Wenhua'),
('330', 'Zhongzheng Rd', '1', 'Taoyuan', 'Taoyuan', 'R5', 'Z', 'Z', '03', '330', 'U5', 'Zhongzheng');

-- Additional DSAGAS and DGDailyCarD records
INSERT INTO [dbo].[DSAGAS] ([COMPNO], [SANO], [SADATE], [CUSTNO], [AMOUNT], [PAYED], [COST], [EMPNO], [EMPNAME], [GTYPE], [CC2], [BB2], [TKG]) VALUES
('C001', 'W250720002', GETDATE()-2, 1002, 1300, 1300, 900, 'E003', 'Peter Jones', '1', 2, 2, 40),
('C001', 'W250720003', GETDATE()-2, 1003, 650, 0, 450, 'E001', 'John Doe', '1', 1, 1, 20),
('C001', 'W250721002', GETDATE()-1, 1004, 720, 720, 500, 'E003', 'Peter Jones', '1', 0, 0, 20),
('C001', 'W250721003', GETDATE()-1, 1005, 550, 0, 380, 'E001', 'John Doe', '1', 1, 1, 16);
INSERT INTO [dbo].[DGDailyCar] ([COMPNO], [IONO], [GIODATE], [GIOTIME], [VENO], [EMPNO], [EMPNAME], [CARSEQ]) VALUES
('C001', 'T250720002', GETDATE()-2, '10:00:00', 'V-GAS1', 'E003', 'Peter Jones', 1),
('C001', 'T250721002', GETDATE()-1, '09:00:00', 'V-GAS1', 'E001', 'John Doe', 1);
INSERT INTO [dbo].[DGDailyCarD] ([COMPNO], [IONO], [BARCODE], [G01], [LASTNO], [YNINI], [SANO]) VALUES
('C001', 'T250720002', 'BC-002', '1', '1002', 'Y', 'W250720002'),
('C001', 'T250720002', 'BC-003', '1', '1002', 'Y', 'W250720002'),
('C001', 'T250720001', 'BC-006', '1', '1003', 'Y', 'W250720003'),
('C001', 'T250721002', 'BC-007', '1', '1004', 'Y', 'W250721002');

-- Remaining Tables
PRINT 'Step 7: Final rapid insertion for remaining tables...';
INSERT INTO [dbo].[ABCASE] (COMPNO, CASENO, CANAME) VALUES 
('C001', 'CASE01', 'Project A'), ('C001', 'CASE02', 'Project B'), 
('C001', 'CASE03', 'Project C'), ('C001', 'CASE04', 'Project D'), 
('C001', 'CASE05', 'Project E');
INSERT INTO [dbo].[ABSUBJ0] (COMPNO, OBJNO, NAME, DC) VALUES 
('C001', 'DUM01', 'Dummy Asset', 'D'), ('C001', 'DUM02', 'Dummy Liability', 'C'),
('C001', 'DUM03', 'Dummy Equity', 'C'), ('C001', 'DUM04', 'Dummy Revenue', 'C'),
('C001', 'DUM05', 'Dummy Expense', 'D');
INSERT INTO [dbo].[BAccShift] (COMPNO, BACNO, BATYPE) VALUES 
('C001', 'A01', 'Daily Sales'), ('C001', 'A02', 'Daily Collection'),
('C001', 'B01', 'Daily Purchase'), ('C001', 'B02', 'Daily Payment'),
('C001', 'C01', 'Misc Expense');
INSERT INTO [dbo].[BAccShiftD] (COMPNO, BACNO, DC, OBJNO, SORM) VALUES 
('C001', 'A01', 'D', '1102', 'M'), ('C001', 'A01', 'C', '4101', 'M'),
('C001', 'A02', 'D', '1101', 'M'), ('C001', 'A02', 'C', '1102', 'M'),
('C001', 'B01', 'D', '5101', 'M');
INSERT INTO [dbo].[BALLBRAND] (BRNO, BRNAME) VALUES 
('B01', 'BrandX'), ('B02', 'BrandY'), ('B03', 'BrandZ'), 
('B04', 'BrandA'), ('B05', 'BrandB');
INSERT INTO [dbo].[BBANK] (COMPNO, BAID, BACANO, BNAME) VALUES 
('C001', 'BK01', '12345', 'Bank of City'), ('C001', 'BK02', '67890', 'National Bank'),
('C001', 'BK03', '11122', 'Credit Union'), ('C001', 'BK04', '33445', 'MegaBank'),
('C001', 'BK05', '55667', 'Local Bank');
INSERT INTO [dbo].[BBSALITEM] (COMP, SALNO, SALNAME) VALUES 
('A', 'S001', 'Base Salary'), ('A', 'S002', 'Commission'),
('A', 'S003', 'Bonus'), ('A', 'D001', 'Insurance'), ('A', 'D002', 'Tax');
INSERT INTO [dbo].[BBDFSALARY] (COMP, COMPNO, EMPNO, SSEQ, SALNO, SMONEY) VALUES 
('A', 'C001', 'E001', 1, 'S001', 50000), ('A', 'C001', 'E002', 1, 'S001', 45000),
('A', 'C001', 'E003', 1, 'S001', 52000), ('A', 'C001', 'E004', 1, 'S001', 60000),
('A', 'C001', 'E005', 1, 'S001', 75000);
INSERT INTO [dbo].[BBHOLIDAY] (DHDATE, HDESC) VALUES 
('2025-01-01', 'New Year'), (GETDATE()-10, 'Holiday A'),
(GETDATE()-20, 'Holiday B'), (GETDATE()-30, 'Holiday C'),
(GETDATE()-40, 'Holiday D');
INSERT INTO [dbo].[BBRAND] (TPNO1, TPNO2, BRNO, BRNAME) VALUES 
('1', '1', 'B01', 'Stove Brand A'), ('1', '1', 'B02', 'Stove Brand B'),
('1', '2', 'B01', 'Regulator X'), ('1', '2', 'B02', 'Regulator Y'),
('2', '1', 'B01', 'Hose Brand Z');
INSERT INTO [dbo].[BCusPhoto] (COMPNO, CUSTNO, PSEQ, DESCRIBE) VALUES 
('C001', 1001, 1, 'Installation'), ('C001', 1001, 2, 'Meter Reading'),
('C001', 1002, 1, 'Kitchen Setup'), ('C001', 1002, 2, 'Contract Signed'),
('C001', 1003, 1, 'Front Door');
INSERT INTO [dbo].[BEventConv] (BFNO, EVNO, EVNAME) VALUES 
('E1', 'EV01', 'Low Battery'), ('E1', 'EV02', 'Tamper Alert'),
('E1', 'EV03', 'Leak Detected'), ('E1', 'EV04', 'Signal Lost'),
('E1', 'EV05', 'Maintenance Due');
INSERT INTO [dbo].[BFlowMeter] (COMPNO, CUSTNO, BFSEQ, FLTYPE, GID) VALUES 
('C001', 1002, 1, 'Commercial', 'METER-001'), ('C001', 1002, 2, 'Sub Meter', 'METER-002'),
('C001', 1004, 1, 'Standard', 'METER-003'), ('C001', 1005, 1, 'Standard', 'METER-004'),
('C001', 1001, 1, 'Standard', 'METER-005');
INSERT INTO [dbo].[BFlowPrice] (COMPNO, CUSTNO, BFSEQ, SDATE, PRICE) VALUES 
('C001', 1002, 1, GETDATE()-365, 30.5), ('C001', 1002, 2, GETDATE()-365, 32.0),
('C001', 1004, 1, GETDATE()-365, 31.0), ('C001', 1005, 1, GETDATE()-365, 31.0),
('C001', 1001, 1, GETDATE()-365, 31.0);
INSERT INTO [dbo].[BFvend] (BFNO, FNAME) VALUES 
('V1', 'Vendor A'), ('V2', 'Vendor B'), ('V3', 'Vendor C'), 
('V4', 'Vendor D'), ('V5', 'Vendor E');
INSERT INTO [dbo].[BGASQTY] (COMPNO, VENO, LADATE, FF1, EE1) VALUES 
('C001', 'E001', GETDATE(), 10, 5), ('C001', 'E003', GETDATE(), 12, 3),
('C001', 'V-GAS1', GETDATE(), 500, 20), ('C001', 'V-CYL1', GETDATE(), 0, 0),
('C001', 'E005', GETDATE(), 0, 0);
INSERT INTO [dbo].[BGSALARYD] (COMP, COMPNO, SALYM, SALTP, EMPNO, SSEQ, SALNO, AMOUNT) VALUES 
('A', 'C001', '2025-06', 'M', 'E001', 1, 'S001', 50000),
('A', 'C001', '2025-06', 'M', 'E002', 1, 'S001', 45000),
('A', 'C001', '2025-06', 'M', 'E003', 1, 'S001', 52000),
('A', 'C001', '2025-06', 'M', 'E004', 1, 'S001', 60000),
('A', 'C001', '2025-06', 'M', 'E005', 1, 'S001', 75000);
INSERT INTO [dbo].[BGSALARYM] (COMP, COMPNO, SALYM, SALTP, EMPNO, TWAGES) VALUES 
('A', 'C001', '2025-06', 'M', 'E001', 50000), ('A', 'C001', '2025-06', 'M', 'E002', 45000),
('A', 'C001', '2025-06', 'M', 'E003', 52000), ('A', 'C001', '2025-06', 'M', 'E004', 60000),
('A', 'C001', '2025-06', 'M', 'E005', 75000);
INSERT INTO [dbo].[BInvComp] (COMPNO, UNIFYNO, CNAME) VALUES 
('C001', '12345678', 'Global Gas'), ('C001', '87654321', 'Regional Propane'),
('C001', '11223344', 'City Gasworks'), ('C001', '55667788', 'Suburban Fuel'),
('C001', '99887766', 'Industrial Gases');
INSERT INTO [dbo].[BIP] (COMPNO, BSEQM, BSEQ, IP) VALUES 
('C001', 'M01', 'S01', '192.168.1.100'), ('C001', 'M01', 'S02', '192.168.1.101'),
('C001', 'M01', 'S03', '192.168.1.102'), ('C001', 'M02', 'S01', '192.168.2.100'),
('C001', 'M02', 'S02', '192.168.2.101');
INSERT INTO [dbo].[BIPM] (COMPNO, BSEQM, IP, COMPUTER) VALUES 
('C001', 'M01', '192.168.1.1', 'Main Router'), ('C001', 'M02', '192.168.2.1', 'Branch Router'),
('C001', 'M03', '10.0.0.1', 'HQ Router'), ('C001', 'M04', '10.10.0.1', 'SiteB Router'),
('C001', 'M05', '172.16.0.1', 'Factory Router');
INSERT INTO [dbo].[BKIND1] (TPNO1, TPNAME, ISBARCODE) VALUES 
('1', 'Appliances', 'N'), ('2', 'Services', 'N'), ('3', 'Parts', 'Y'),
('4', 'Consumables', 'Y'), ('5', 'Rental', 'Y');
INSERT INTO [dbo].[BKIND2] (TPNO1, TPNO2, TPNAME) VALUES 
('1', 'A', 'Stoves'), ('1', 'B', 'Regulators'), ('1', 'C', 'Hoses'),
('2', 'A', 'Inspection'), ('2', 'B', 'Repair');
INSERT INTO [dbo].[DGasCounter] (COMPNO, CUSTNO, BFSEQ, GDATE, QTY) VALUES 
('C001', 1002, 1, GETDATE()-30, 150.5), ('C001', 1002, 1, GETDATE(), 250.0),
('C001', 1002, 2, GETDATE()-30, 50.1), ('C001', 1002, 2, GETDATE(), 85.2),
('C001', 1004, 1, GETDATE()-45, 120.0);
INSERT INTO [dbo].[DMessage] (MSNO, MSDATE, MSENDER, MTITLE) VALUES 
('MSG01', GETDATE(), 'E005', 'Announcement'), ('MSG02', GETDATE(), 'E005', 'Holiday Schedule'),
('MSG03', GETDATE(), 'E002', 'Sales Meeting'), ('MSG04', GETDATE(), 'E001', 'Driver Briefing'),
('MSG05', GETDATE(), 'E004', 'Finance Deadline');
INSERT INTO [dbo].[DMessRec] (MSNO, SEQ, RECID, RECNAME) VALUES 
('MSG01', 1, 'E001', 'John Doe'), ('MSG01', 2, 'E002', 'Jane Smith'),
('MSG02', 1, 'E001', 'John Doe'), ('MSG03', 1, 'E002', 'Jane Smith'),
('MSG04', 1, 'E001', 'John Doe');

GO

-- =================================================================
-- Step 8: Finalization - Re-enable All Triggers
-- =================================================================
PRINT 'Step 8: Re-enabling all triggers...';
EXEC sp_msforeachtable "ALTER TABLE ? ENABLE TRIGGER all";
GO

PRINT '=====================================================';
PRINT '      DUMMY DATA INSERTION SCRIPT COMPLETE         ';
PRINT '=====================================================';
GO