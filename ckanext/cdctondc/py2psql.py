#
# author : jiankaiwang (http://jiankaiwang.no-ip.biz/)
# source code in github : seed (https://github.com/jiankaiwang/seed)
# document in gitbook : seed (https://www.gitbook.com/book/jiankaiwang/seed/details)
#

#
# example :
#
# link to postgresql database
# p2l = py2psql("127.0.0.1","5432","ckan_default","public.user","ckan_default","ckan")
#
# returned status : call status()
# { "state" : [success|failure|warning], "info" : "message", "data" : []}
#
# example.1 get table schema
# 1.1
# p2l = py2psql("127.0.0.1","5432","ckan_default","public.user","ckan_default","ckan")
# p2l.getTableSchema()  # default table, only fetches column name(desc[0])
# 1.2
# p2l2 = py2psql("127.0.0.1","5432","ckan_default","","ckan_default","ckan")
# p2l2.getTableSchema("public.user",0)  # desired table
# p2l2.getTableSchema("public.user",-1)  # fetch all description
# p2l.status()
#
# example.2 query data
# 2.1 select column name, email, 123 (not existing)
# data = p2l.select({where},[columns])
# data = p2l.select({"name":"test114"},["name","email","123"])
# data = p2l.select({"name":"test114"},[])
# 2.2 select column name, email, 123 (not existing) and also returned as dictionary
# data = p2l.select({where},[columns],asdict=True)
# data = p2l.select({"name":"test114"},["name","email","123"],asdict=True)
# data = p2l.select({"name":"test114"},[],asdict=True)
#
# example.3 update data
# 3.1
# p2l.update({set},{where})
# p2l.update({"email":"test@tw"},{"name":"test114"})
#
# example.4 insert data
# 4.1
# p2l.insert({ data })
# p2l.insert({ "id" : "acbdhcbdh-abchdbch", "name":"123","email":"123@tw" })
#
# example.5 delete data
# 5.1
# p2l.delete({where})
# p2l.delete({"name":"test1", "email":"test1@tw"})
#
# example.6 execsql data
# 6.1 only one function can create object without assigning table
# p2l.execsql("sql command", is there returned value, {parameter : value})
# p2l.execsql("select * from public.user where name = %(name)s;", True, {'name' : "test114"}, True)
# p2l.status()
# 6.2 get table list
# p2l.execsql("select * from information_schema.tables where table_name = %(name)s;", True, {'name' : "user"})
# p2l.status()
#
# example.7 create data table
# 7.1 drop first
# p2l.createTable("test", {"id" : "serial primary key", "context" : "text not null"}, dropFirst=True)
# p2l.status()
#
# example.8 alter data table
# 8.1 
# p2l.alterTable("test", {"context" : "text"}, createTableFirstIfNotExisted=False, addColIfNotExisted=False, theSameWithThisSchema=True)
# p2l.status()
#
# example.9 drop data table
# 9.1
# p2l.dropTable("test")
# p2l.status()
#

import psycopg2

class py2psql:
    
    # private member
    # host : URL or IP
    # port : postgresql server port
    # db : as a string
    # tb : as a string
    # user : as a string
    # pwd : as a string
    # data : as a dictionary, { colName : colValue }
    # columns : save table schema
    # datatype : save column data tpye { "col" : { "type" : "code", "null" : "True/False" } }
    # retStatus : returned data as a dictionary
    __host = ""
    __port = ""
    __db = ""
    __tb = ""
    __user = ""
    __pwd = ""
    __columns = []
    __datatype = {}
    __retStatus = { }

    #
    # desc : constructor
    # param@getTB : can be null when only using execsql()
    #
    def __init__(self, getHost, getPort, getDB, getTB, getUser, getPwd):
        self.__host = getHost
        self.__port = getPort
        self.__db = getDB
        self.__tb = getTB
        self.__user = getUser
        self.__pwd = getPwd
        self.__columns = []
        self.__datatype = {}
        self.__retStatus = { "state" : 0, "data" : {}, "info" : "" }

        # fetch column information
        if len(getTB) > 0:
            self.__tableSchema()

    # ------------------------
    # private member
    # ------------------------            
    #
    # desc : define server DSN
    # retn : string
    #
    def __serverDSN(self):
        conStr = ["host=" + self.__host, "port=" + self.__port, "dbname=" + self.__db, "user=" + self.__user , "password=" + self.__pwd]
        return ' '.join(conStr)

    #
    # desc : get table schema
    # retn : None
    #
    def __tableSchema(self):
        # Connect to an existing database
        conn = psycopg2.connect(self.__serverDSN())
        
        # Open a cursor to perform database operations
        cur = conn.cursor()

        # select sql
        selectStr = "select * from " + self.__tb

        cur.execute(selectStr)
        
        # get columns
        self.__columns = [desc[0] for desc in cur.description]

        # close communication
        cur.close()
        conn.close()

    #
    # desc : get table colunm data type
    # retn : column data type in the table
    #
    def __tableColDatatype(self):
        # Connect to an existing database
        conn = psycopg2.connect(self.__serverDSN())
        
        # Open a cursor to perform database operations
        cur = conn.cursor()

        # select sql
        selectStr = "select * from " + self.__tb

        cur.execute(selectStr)
        
        # get column data type
        for item in cur.description:
            self.__datatype.setdefault(item[0], { "type" : item[1] , "null" : item[6] })
        
        # close communication
        cur.close()
        conn.close()

        return self.__datatype
        
        
    #
    # desc : get col index in the column order
    # retn : -1 (None) or Number
    #
    def __getColIndex(self, getColName):
        if getColName in self.__columns:
            return self.__columns.index(getColName)
        else:
            return -1

    #
    # desc : set returned status
    # retn : None
    #
    def __setStatus(self, getStatus, getInfo, getData):
        self.__retStatus["state"] = getStatus
        self.__retStatus["data"] = getData
        self.__retStatus["info"] = getInfo

    #
    # desc : get column description on the execution pointer
    # param@getCur : a psycopg2 connect cursor
    # param@curIndex : index on the cursor description
    # retn : [] data type
    #
    def __getCurDesc(self, getCur, curIndex):
        curInfo = [desc[curIndex] for desc in getCur.description]
        return curInfo

    # ------------------------
    # public member
    # ------------------------  
                
    #
    # desc : returned status
    # retn : return executing status
    #
    def status(self):
        return self.__retStatus
    
    #
    # desc : get table schema
    # param@getTable : get desired table schema
    # param@descIndex : description index of table schema, -1 : means all
    # retn : status object
    #
    def getTableSchema(self, getTable=None, descIndex=0):    
        if self.__tb == "" and getTable == None:
            self.__setStatus("failure","There is no table assigned.",{})
        elif self.__tb != "" and getTable == None:
            try:
                self.__tableSchema()
                self.__setStatus("success","Get the table schema.", self.__columns)
            except:
                self.__setStatus("failure","Can not get the table schema.", self.__columns)
        elif getTable != None:
            # Connect to an existing database
            conn = psycopg2.connect(self.__serverDSN())
        
            # Open a cursor to perform database operations
            cur = conn.cursor()

            # select sql
            selectStr = "select * from " + getTable

            try:
                cur.execute(selectStr)
        
                # get columns desc
                if descIndex < 0:
                    getColDesc = [desc for desc in cur.description]
                else:
                    getColDesc = [desc[descIndex] for desc in cur.description]
                self.__setStatus("success","Get the table schema.", getColDesc)
            except:
                self.__setStatus("failure","Can not get the table schema.", {})

            # close communication
            cur.close()
            conn.close()             
            
        return self.__retStatus
                
    #
    # desc : select operation
    # param@getConds : {}, defined where SQL conditions
    # param@getParams : [], selected column names, empty : means all
    # param@asdict : boolean, returned row as dictionary data type
    # retn : data as [] type
    # note : also support status object, use status()
    #
    def select(self, getConds, getParams, asdict=False):
        # filter the column value
        colSelected = "*"
        colList = []
        retdata = []
        dataTuple = ()
        
        # check column existing
        if len(getParams) > 0:
            for item in getParams:        
                if self.__getColIndex(item) > -1:
                    colList.append(item)
        
        # set selected columns
        if len(colList) > 0:
            colSelected = ','.join(colList)

        try:
                                
            # Connect to an existing database
            conn = psycopg2.connect(self.__serverDSN())
            
            # Open a cursor to perform database operations
            cur = conn.cursor()
    
            # select sql
            selectStr = "select " + colSelected + " from " + self.__tb
    
            if len(getConds.keys()) > 0:
                selectStr += " where "
                item = 0
                for key, value in getConds.iteritems():
                    if item != 0:
                        selectStr += " and "
                    selectStr += str(key) + "= %s "
                    item += 1
                    dataTuple += (value,)
            selectStr += ";"                                                
        
            # parameter-based select sql
            cur.execute(selectStr, dataTuple)
    
            # get all data    
            rawdata = cur.fetchall()
            
            # modify data to customized type
            if asdict:
                if len(colList) > 0:
                    for pair in rawdata:
                        tmpDict = {}
                        for item in range(0,len(pair),1):
                            tmpDict.setdefault(colList[item],pair[item])
                        retdata.append(tmpDict)
                else:
                    for pair in rawdata:
                        tmpDict = {}
                        for item in range(0,len(pair),1):
                            tmpDict.setdefault(self.__columns[item],pair[item])
                        retdata.append(tmpDict)
            else:
                retdata = rawdata
                
            # close communication
            cur.close()
            conn.close()          
        
            # set status
            self.__setStatus("success", "Select operation succeeded.", retdata)

        except:
            self.__setStatus("failure", "Select operation executed failed.", retdata)
                                               

        return retdata

    #
    # desc : update operation
    # param@getParams : {}, set sql parameters    
    # param@getConds : {}, where sql conditions
    # retn : 0 : failure, 1 : success
    # note : also support status object, use status()
    #
    def update(self, getParams, getConds):
        # 0 : failure, 1 : success
        retStatus = 1
    
        # filter the column value
        paraKeys = getParams.keys()
        condKeys = getConds.keys()
        paraList = []
        condList = []
        dataTuple = ()
        
        # check parameter existing
        if len(paraKeys) > 0:
            for item in paraKeys:     
                if self.__getColIndex(item) > -1:
                    paraList.append(item)
        else:
            retStatus = 0
            self.__setStatus("failure","Set SQL was checked in failure.",{})
            return retStatus
        
        # check condition existing
        if len(condKeys) > 0:
            for item in condKeys:     
                if self.__getColIndex(item) > -1:
                    condList.append(item)
        else:
            retStatus = 0
            self.__setStatus("failure","Where SQL was checked in failure.",{})
            return retStatus

        # update sql
        updateStr = "update " + self.__tb + " set "
        
        if len(paraList) > 0:
            paraListItem = []
            for item in paraList:
                paraListItem.append(item + "= %s ")
                dataTuple += (getParams[item],)
            updateStr += ' , '.join(paraListItem)
        else:
            retStatus = 0
            self.__setStatus("failure","Set SQL was checked in failure.",{})
            return retStatus
            
        updateStr += " where "

        if len(condList) > 0:
            condListItem = []
            for item in condList:
                condListItem.append(item + "= %s ")
                dataTuple += (getConds[item],)
            updateStr += ' and '.join(condListItem)
        else:
            retStatus = 0
            self.__setStatus("failure","Where SQL was checked in failure.",{})
            return retStatus
        
        updateStr += ";"                     

        try:
            # Connect to an existing database
            conn = psycopg2.connect(self.__serverDSN())
            
            # Open a cursor to perform database operations
            cur = conn.cursor()     
    
            # parameter-based update sql
            cur.execute(updateStr, dataTuple)
    
            # get all data    
            conn.commit()
    
            # close communication
            cur.close()
            conn.close()       
            
            self.__setStatus("success","Update operation succeeded.",{})
            
        except:      
                                
            retStatus = 0
            self.__setStatus("failure","Update operation was executed in failure.",{})

        return retStatus        
        
    #
    # desc : insert operation
    # param@getParams : {}, value sql parameters    
    # retn : 0 : failure, 1 : success
    # note : also support status object, use status()
    #
    def insert(self, getParams):
        # 0 : failure, 1 : success
        retStatus = 1
    
        # filter the column value
        paraKeys = getParams.keys()
        paraList = []
        insertedData = ()
        
        # check parameter existing
        if len(paraKeys) > 0:
            for item in paraKeys:     
                if self.__getColIndex(item) > -1:
                    paraList.append(item)
        else:
            retStatus = 0
            self.__setStatus("failure","Data parameter was empty.",{})
            return retStatus
            
        # insert string
        insertStr = "insert into " + self.__tb + " ("
        
        for index in range(0,len(paraList),1):
            if index != 0:
                insertStr += ', '
            insertStr += paraList[index]
        
        insertStr += ') values ('
        
        for index in range(0,len(paraList),1):
            if index != 0:
                insertStr += ', '
            insertStr += "%s"
            insertedData += (getParams[paraList[index]],)
        
        insertStr += ')'
        
        try:
        
            # Connect to an existing database
            conn = psycopg2.connect(self.__serverDSN())
            
            # Open a cursor to perform database operations
            cur = conn.cursor()     

            # parameter-based insertion sql
            cur.execute(insertStr,insertedData)

            # get all data    
            conn.commit()

            # close communication
            cur.close()
            conn.close()
            
            self.__setStatus("success","Insert operation succeeded.",{})
        
        except:
            self.__setStatus("failure","Insert operation was executed in failure.",{})
            retStatus = 0
        
        return retStatus

    #
    # desc : delete operation
    # param@getConds : {}, where sql conditions
    # retn : 0 : failure, 1 : success
    # note : also support status object, use status()
    #
    def delete(self, getConds):
        # 0 : failure, 1 : success
        retStatus = 1
    
        # filter the column value
        condKeys = getConds.keys()
        condList = []
        selectedTuple = ()
        
        # check parameter existing
        if len(condKeys) > 0:
            for item in condKeys:     
                if self.__getColIndex(item) > -1:
                    condList.append(item)
        else:
            retStatus = 0
            self.__setStatus("failure","Where parameter was empty.",{})
            return retStatus

        # no where condition
        if len(condList) < 1:
            retStatus = 0
            self.__setStatus("failure","Value in where parameter was empty.",{})
            return retStatus
            
        # delete string
        deleteStr = "delete from " + self.__tb + " where "
        
        for index in range(0,len(condList),1):
            if index != 0:
                deleteStr += ' and '
            deleteStr += condList[index] + " = " + "%s"
            selectedTuple += (getConds[condList[index]],)
            
        # delete transaction
        try:
        
            # Connect to an existing database
            conn = psycopg2.connect(self.__serverDSN())
            
            # Open a cursor to perform database operations
            cur = conn.cursor()     

            # parameter-based sql
            cur.execute(deleteStr, selectedTuple)

            # get all data    
            conn.commit()

            # close communication
            cur.close()
            conn.close()
            
            self.__setStatus("success","Delete operation succeeded.",{})
        
        except:
            self.__setStatus("failure","Delete operation was executed in failure.",{})
            retStatus = 0
        
        return retStatus

    #
    # desc : execute complex sql command
    # param@getSQL : parameter-based complex sql command
    # e.g. "select * from public.user where name = %(name)s;"
    # param@hasRetValue : are there returned values ?
    # param@getParams : {}
    # e.g. {'name' : "test114"}
    # param@asdict : only works when param@hasRetValue is true, returned value as dictionary data type
    # retn : return executing status
    #
    def execsql(self, getSQL, hasRetValue, getParams, asdict=True):
        # save returned data as dictionary data type
        retData = []
        
        # check data type is allowed
        if not isinstance(getParams, dict):
            self.__setStatus("failure", "Parameters must be as dictionary type.", {})
            return
        
        try:
            # connect to db       
            conn = psycopg2.connect(self.__serverDSN())
        except:
            self.__setStatus("failure", "Can not connect to db.", {})
            return

        try:
            # Open a cursor to perform database operations
            cur = conn.cursor()
        
            # parameter-based select sql
            cur.execute(getSQL, getParams)
        except:
            self.__setStatus("failure", "SQL was executed in failure.", {})
            return
        
        rawdata = {}
        try:
            if hasRetValue:
                # select
                
                # get columns
                execColumns = self.__getCurDesc(cur, 0)
                
                # get all data	
                rawdata = cur.fetchall()
                
                if asdict:
                    # set transform tuple data type into dictionary data type
                    tmp = {}
                    for item in range(0, len(rawdata), 1):
                        tmp = {}
                        for col in range(0, len(execColumns), 1):
                            tmp.setdefault(execColumns[col], rawdata[item][col])
                        retData.append(tmp)
            else:
                # insert, delete, update
                conn.commit()
            
            # close communication
            cur.close()
            conn.close()

        except:
            self.__setStatus("failure", "Data can not be queried or SQL command can not be executed.", {})
            return

        if hasRetValue:
            if asdict:
                self.__setStatus("success", "SQL command was executed.", retData)
            else:
                self.__setStatus("success", "SQL command was executed.", rawdata)
        else:
            self.__setStatus("success", "SQL command was executed.", {})
        return	

    #
    # desc : create table based on schema
    # param@tableName : name of the table for creation
    # param@tableSchema : { 'colName' : 'colSchema', '' : '' }
    # param@dropFirst : whether to drop table first if it exists
    # retn : None, call status() to get status object
    #
    def createTable(self, tableName, tableSchema, dropFirst=False):
        
        if not (isinstance(tableSchema, dict)):
            self.__setStatus("failure", "Parameters are not correct.", {})
            return
            
        # check table status (whether it exists or not)
        try:
            self.execsql("select * from information_schema.tables where table_name = %(name)s;", True, {'name' : tableName})
        except:
            self.__setStatus("failure", "Can not get the table list.", {})
            return
            
        if self.__retStatus["state"] != "success":
            self.__setStatus("failure", "Can not check table status.", {})
            return
        
        if len(self.__retStatus["data"]) > 0:
            # table already exists
            if dropFirst:
                # delete first
                self.execsql("drop table if exists " + tableName + ";", False, {})
                
                if self.__retStatus["state"] != "success":
                    self.__setStatus("failure", self.__setStatus["data"] + " Can not drop the data table.", {})
                    
            else:
                self.__setStatus("failure", "The table already exists, if it does not drop, the table can not be created.", {})
                return

        # create table
        tmpKey = tableSchema.keys()
        createTBCmd = "create table if not exists " + tableName + " ( "
        for colIndex in range(0, len(tmpKey), 1):
            if colIndex != 0:
                createTBCmd += ', '
            createTBCmd += tmpKey[colIndex] + " " + tableSchema[tmpKey[colIndex]]
        createTBCmd += " );"
            
        try:
            self.execsql(createTBCmd, False, {})
        except:
            self.__setStatus("failure", "Unexcepted error on creating the data table.", {})
            return
        
        if self.__retStatus["state"] != "success":
            self.__setStatus("failure", "Can not create data table.", {})
            return
        else:
            self.__setStatus("success", "Create data table successfully.", {})

    #
    # desc : alter table schema
    # param@tableName : table for altering
    # param@tableSchema : { 'colName' : 'new col schema' }
    # param@createTableFirstIfNotExisted : whether to create table first if table does not exist
    # param@addColIfNotExisted : whether to add column if it does not exist
    # param@theSameWithThisSchema : whether to fit the table with the input schema
    # retn : None, call status() to get status object
    # note : if addColIfNotExisted == False, the column for altering would be skipped 
    #
    def alterTable(self, \
                   tableName, \
                   tableSchema, \
                   createTableFirstIfNotExisted=True, \
                   addColIfNotExisted=True,\
                   theSameWithThisSchema=True):
        
        if not (\
                isinstance(tableName, str) and \
                isinstance(tableSchema, dict) and\
                isinstance(createTableFirstIfNotExisted, bool) and\
                isinstance(addColIfNotExisted, bool)
               ):
            self.__setStatus("failure", "Parameters are not correct.", {})
            return    
    
        # check table status (whether it exists or not)
        try:
            self.execsql("select * from information_schema.tables where table_name = %(name)s;", True, {'name' : tableName})
        except:
            self.__setStatus("failure", "Can not get the table list.", {})
            return
            
        if self.__retStatus["state"] != "success":
            self.__setStatus("failure", "Can not check table status.", {})
            return
        
        # table does not exist
        if len(self.__retStatus["data"]) < 1:
            if createTableFirstIfNotExisted:
                # create table first
                self.createTable(tableName, tableSchema, False)
                
                if self.__retStatus["state"] != "success":
                    self.__setStatus("failure", self.__retStatus["info"] + " Can not create the data table.", {})
                    return
            else:
                self.__setStatus("failure", "The table does not exist, if it does not be created, the alter operation would be stop.", {})
                return
        # table exists
        else:
            # get table column name
            crtColName = self.getTableSchema(tableName, 0)['data']
            
            warningFlag = 0
            warningMsg = ""
            for name, schema in tableSchema.iteritems():
                if name in crtColName:
                    # the same column name
                    self.execsql(\
                        "alter table " + tableName + " alter column " + name + " type " + schema + " ;",
                        False,
                        {},
                        False
                    )
                    
                    if self.__retStatus["state"] != "success":
                        warningFlag = 1
                        warningMsg = warningMsg + ' [alter column failure]' + self.__retStatus["info"]

                    # remove the column from the list
                    # the left column in the list may be dropped
                    crtColName.remove(name)
                else:
                    # there is no existing column
                    if addColIfNotExisted:
                        self.execsql(\
                            "alter table " + tableName + " add column " + name + " " + schema + " ;",
                            False,
                            {},
                            False
                        )
                        
                        if self.__retStatus["state"] != "success":
                            warningFlag = 1
                            warningMsg = warningMsg + ' [add column failure]' + self.__retStatus["info"]
                    else:
                        warningFlag = 1
                        warningMsg = warningMsg + ' [not to add column] The column ' + name + ' does not exist and also not to create if it does not exist.'
            
            # drop the other column 
            if theSameWithThisSchema:
                for colName in crtColName:
                    self.execsql(\
                            "alter table " + tableName + " drop column if exists " + colName + " ;",
                            False,
                            {},
                            False
                        )

                    if self.__retStatus["state"] != "success":
                        warningFlag = 1
                        warningMsg = warningMsg + ' [drop column failure] ' + colName + ' ' + self.__retStatus["info"]
            
            if warningFlag == 1:
                self.__setStatus("warning",warningMsg,{})
            else:
                self.__setStatus("success","Alter table completely.",{})
    
    #
    # desc : drop table
    # param@tableName : table for droping
    # retn : None, call status() to get status object
    #
    def dropTable(self, tableName):
        if not (isinstance(tableName, str)):
            self.__setStatus("failure", "Parameters are not correct.", {})
            return    
    
        # check table status (whether it exists or not)
        try:
            self.execsql("select * from information_schema.tables where table_name = %(name)s;", True, {'name' : tableName})
        except:
            self.__setStatus("failure", "Can not get the table list.", {})
            return
            
        if self.__retStatus["state"] != "success":
            self.__setStatus("failure", "Can not check table status.", {})
            return

        if len(self.__retStatus["data"]) > 0:
            # table exist
            self.execsql("drop table if exists " + tableName + ";", False, {}, False)
            
            if self.__retStatus["state"] == "success":
                self.__setStatus("success", "Drop table " + tableName + " successfully.", {})
            else:
                self.__setStatus("failure", "Can not drop table " + tableName + ".", {})
        else:
            # table does not exist
            self.__setStatus("success", "Table " + tableName + " does not exist.", {})
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    