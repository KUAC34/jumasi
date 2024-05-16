#sql.py
import functions

def OeApp_raw(): 
    return f"""SELECT MATNR "M-Code",
        ZGUBUN "Status",
        ZCARMAKER1 "Car Maker",
        ZCARMAKER2 "Sales Brand",
        ZVEHICLE1 "Vehicle Model(Global)",
        ZVEHICLE2 "Vehicle Model(Local)",
        ZPROJECT "Project",
        NVL(NULLIF(ZELECTRIC,' '),'ICE') AS "EV",
        ZSIZE "Size",
        ZLOAD_INDEX "LI/SS", 
        ZPLY "PR", 
        ZTYPE "Pattern", 
        ZL "Load",
        ZW "B", 
        ZUSE "USE", 
        ZBR "Brand",
        ZPRODUCT "Prod Name", 
        LBTXT "PLANT", 
        ZOEPLANT "OE PLANT", 
        ZSOP "SOP", 
        ZEOP "EOP"
        FROM HKT_DW.BI_DWUSER.SAP_ZSTT70041
        """ 


def OeApp_byPlant() :
    return """
            SELECT 
            LBTXT "PLANT",
            COUNT(DISTINCT MATNR) "M-Code"
            FROM HKT_DW.BI_DWUSER.SAP_ZSTT70041
            WHERE ZGUBUN = 'Supplying'
            GROUP BY LBTXT
            """     

# TEST
def OeSellIn(StartDate, EndDate, mCode) :
    return f"""
            SELECT *
            FROM HKT_DW.BI_DWUSER.SAP_ZSDT02068
            WHERE bill_date Between '{StartDate}' and '{EndDate}'
            AND zoereseg = 'OE'
            AND material = '{mCode}'
            """

# OE QI 산출 DATA
def OeSellIn_Monthly_byPlant() :
    # SAP_ZSDT02068 : SellIn Data
    # SAP_ZSTT70041 : OE Applicatoin
    
    return """
            SELECT 
                OeApp.LBTXT AS "PLANT", 
                SellIn.BILMON "YYYYMM",
                OeApp.ZCARMAKER1 "OEM",
                SUM(SellIn.quantity) "Supplies"
            FROM HKT_DW.BI_DWUSER.SAP_ZSDT02068 AS SellIn
            LEFT JOIN ( SELECT 
                            DISTINCT LBTXT, MATNR, ZCARMAKER1
                        FROM 
                            HKT_DW.BI_DWUSER.SAP_ZSTT70041
                        ) AS OeApp ON SellIn.material = OeApp.MATNR
            WHERE 
                SellIn.zoereseg = 'OE'
                AND bill_date >= '20240101'
                AND OeApp.LBTXT IS NOT NULL
            GROUP BY 
                OeApp.LBTXT, 
                SellIn.BILMON,
                OeApp.ZCARMAKER1
            ORDER BY
                PLANT,
                YYYYMM
            """

### CQMS Quality Issue Main DB
def QI_MAIN_Global() : 
    return """
        select
            A.PLANT,
            CASE 
                WHEN A.PLANT IN ('KP', 'DP', 'IP') THEN 'G.OE Quality'
                WHEN A.PLANT IN ('JP', 'HP', 'CP') THEN 'China OE Quality'
                WHEN A.PLANT IN ('MP') THEN 'Euroup OE Quality'
                WHEN A.PLANT IN ('TP') THEN 'NA OE Quality'
                ELSE 'G.OE Quality'
                END "OEQ Group",
            A.OEM,
            A.VEH_MODEL,
            A.PROJECT,
            A.OWNER_NO,
            E.NACHN,
            A.RESPONSIBLE_PERSON_NO,
            A.IS_HK_FAULT,
            A.OCCURRENCE_DATE Occ_D,
            TO_CHAR(A.CREATE_DATE, 'YYYY-MM-DD') AS Reg_D,
            TO_CHAR(A.CREATE_DATE, 'YYYYMM') AS YYYYMM,
            A.RETURN_TIRE_YN Return,
            A.RETURN_TIRE_RECEIVED_DATE Return_D,
            TO_CHAR(A.CQMS_ISSUE_ISSUE_ARENA_APPROVAL_DATE, 'YYYY-MM-DD') IssueReg_D,
            TO_CHAR(A.ISSUE_COMPLETE_DATE, 'YYYY-MM-DD') Complete_Date,
            CASE A.OE_QUALITY_ISSUE_STATUS
                    WHEN 'ISSUE_PROCESS_COMPLETE' THEN 'Complete'
                    ELSE 'On-going'
                END Status,
            D.DATA_NM Type,
            C.DATA_NM CAT,
            B.DATA_NM Sub_CAT,
            DECODE(A.ISSUE_AREA, 
                '01', 'In-Line(OE)',
                '02', 'Field',
                '03', 'Warehouse',
                '04', 'Test',
                '05', 'Internal',
                '06', 'Non-official(In-line)'
                ) Location,
            DECODE(A.ISSUE_AREA,
                '01', 'Include',
                '02', 'Include',
                '03', 'Include',
                '04', 'Include',
                '05', 'Exclude',
                '06', 'Exclude'
                ) KPI,
            DECODE(A.ISSUE_REGION,
                '01', 'Europe',
                '02', 'Africa',
                '03', 'ASIA(China)',
                '04', 'ASIA(Japan)',
                '05', 'ASIA(Korea)',
                '06', 'ASIA(South East)',
                '07', 'Australia',
                '08', 'North America',
                '09', 'South America',
                '10', 'ETC'
                ) Market,
            A.CQMS_ISSUE_DOCUMENT_NO "Doc No",
            A.CQMS_QUALITY_ISSUE_SEQ URL
        from HKT_DW.EQMSUSER.CQMS_QUALITY_ISSUE A
        LEFT JOIN HKT_DW.EQMSUSER.CQMS_ISSUE_CATEGORY_DATA B ON A.ISSUE_CATEGORY_SEQ_3 = B.SEQ
        LEFT JOIN HKT_DW.EQMSUSER.CQMS_ISSUE_CATEGORY_DATA C ON A.ISSUE_CATEGORY_SEQ_2 = C.SEQ
        LEFT JOIN HKT_DW.EQMSUSER.CQMS_ISSUE_CATEGORY_DATA D ON A.ISSUE_CATEGORY_SEQ_1 = D.SEQ
        LEFT JOIN HKT_DW.BI_GERPUSER.ZHRT90041 E ON A.OWNER_NO = E.PERNR
        WHERE IS_OE_RE = ('oe') 
            AND A.OCCURRENCE_DATE LIKE '2024%'
            AND A.STAGE = '02'
            AND (A.IS_HK_FAULT = 'Y' or A.IS_HK_FAULT IS NULL)
            AND DECODE(A.ISSUE_AREA,
                '01', 'Include',
                '02', 'Include',
                '03', 'Include',
                '04', 'Include',
                '05', 'Exclude',
                '06', 'Exclude'
                ) = 'Include'
        ORDER BY A.START_DATE DESC
    """
    
    
