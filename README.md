# TongHuaShunSpider
同花顺上市公司基础信息爬虫
##使用方法
安装好环境后直接运行main文件



针对读者：入门
语言：python
目标：爬取上市公司的股票代码、公司简称、公司全称、创办日期、上市日期、历史年度营收数据、总市值。

##结果展示

       { "_id" : { "$oid" : "5c41949eea12859f21423955" },
         "share_id" : "000506",
         "market_value" : "2954276500.000", 
         "revenue" : [ "7.69亿", "8.12亿", "13.88亿", "3.57亿", "9.07亿", "10.71亿", "13.27亿", "11.97亿", "10.07亿", "8.97亿", "6.97亿", "804.36万", "5489.42万", "2.09亿", "3.14亿", "3.71亿", "3.44亿", "2.70亿", "9841.64万", "1.54亿", "2.48亿", "2.09亿", "2.32亿", "2.25亿", "2.38亿", false ], 
         "year" : [ 2017, 2016, 2015, 2014, 2013, 2012, 2011, 2010, 2009, 2008, 2007, 2006, 2005, 2004, 2003, 2002, 2001, 2000, 1999, 1998, 1997, 1996, 1995, 1994, 1993, 1992 ], 
         "market_time" : "1993-03-12", 
         "start_time" : "1988-05-11", 
         "nick_name" : "中润资源", 
         "name" : "中润资源投资股份有限公司" }

1、在所有公司的入口爬取[公司列表](http://q.10jqka.com.cn/index/index/board/all/field/zdf/order/desc/page/1)，这里可以获取到股票代码以及公司简称。
2、在公司的资料页面，可以获取到公司的全称，里面还有英文名什么的，[例](http://stockpage.10jqka.com.cn/600157/company/)。
3、在公司的财政页面，可以获取到总营收，[例](http://basic.10jqka.com.cn/600157/finance.html)
4、在一个接口，可以获取到公司的总市值、创办时间、上市时间。[例](http://d.10jqka.com.cn/v2/realhead/hs_600157/last.js)
5、将获取到的信息提交到pipeline,并存到MongoDB。

##环境准备
1、[使用scrapy建立一个项目](https://scrapy-chs.readthedocs.io/zh_CN/1.0/intro/overview.html)
2、创建mongo数据库，详细步骤请[百度](https://www.baidu.com)

##实现
新建一个爬虫，我这里名为

        name = "share_main"

添加允许的域名
   
    allowed_domains = [
        "q.10jqka.com.cn",
        "stockpage.10jqka.com.cn",
        "basic.10jqka.com.cn",
        "d.10jqka.com.cn"]
   定义

      rank_base_page = 'http://q.10jqka.com.cn/index/index/board/all/field/zdf/order/desc/page/'

parse方法
根据不同的Url对应不同的处理方法
一共有四种页面：
1、所有上市公司的列表页面
2、公司信息详情页
3、公司财务信息页面
4、公司的年营收接口

       def parse(self, response):
        # 获取页面总数
        if "q.10jqka.com.cn/index/index/board/all/field/zdf/order/desc/page" in response.url:
            max = int(response.xpath("//span[@class='page_info']/text()").extract()[0].split('/')[1])
            print('这是列表页面 一共', max, "页")

            yield from self.handlePage(response)
            for i in range(max):
                if i != 1:
                    yield scrapy.Request(rank_base_page + str(i), self.handlePage)

        elif "company.html" in response.url:
            # print("这是company详情页面")
            self.companyParse(response)
        elif "finance.html" in response.url:
            # print("这是finance详情页面")
            self.financeParse(response)
        elif "d.10jqka.com.cn/v2/realhead" in response.url:
            # print("这是realhead详情页面")
            self.infoParse(response)

在[公司列表](http://q.10jqka.com.cn/index/index/board/all/field/zdf/order/desc/page/1)页面的的处理方法（handlePage）中获取公司简称以及公司的股票代码，
+ 使用response.xpath("//tr")获取所有的tr标签
如下图，第一行是“序号 代码 名称”这一行，使用 trs[1:]截取
![](https://upload-images.jianshu.io/upload_images/3500742-e6f3dbf2a120b98b.png?imageMogr2/auto-orient/strip%7CimageView2/2/w/1240)
+ 遍历tr标签，使用tr.xpath(".//a[@target='_blank']")获取tr标签中所有target='_blank'的a标签（.//表示在当前节点中查找所有符合条件的标签）
text()方法能够获取标签<></>中的文本，这里拿到的就是股票代码与简称
+ 将获取到的股票代码、简称抛出给[Pipeline](https://scrapy-chs.readthedocs.io/zh_CN/1.0/topics/item-pipeline.html)处理
+ 根据获取到的股票代码，生成对应的公司详情、财务详情、以及营收的地址，继续轮询（由于同一个股票代码需要请求三个地址才能够获取全部的信息，所以在请求的时候使用meta加入股票代码，这样处理的时候就知道是哪个股票了）

完整代码如下

     def handlePage(self, response):
        print("处理列表页面")
        trs = response.xpath("//tr")
        for tr in trs[1:]:
            # 股票代码 简称
            a = tr.xpath(".//a[@target='_blank']")

            id = a[0].xpath('text()').extract()[0]
            name = a[1].xpath('text()').extract()[0]
            # print(id, name)

            company = Company()
            company['share_id'] = id
            company['nick_name'] = name
            yield company

            # urls = response.xpath("//tr//a[@target='_blank']/@href").extract()
            # for url in urls:
            #     print(url)
            yield scrapy.Request("http://basic.10jqka.com.cn/" + id + "/company.html", self.companyParse,meta={'share_id': id})
            yield scrapy.Request("http://basic.10jqka.com.cn/" + id + "/finance.html", self.financeParse,meta={'share_id': id})
            yield scrapy.Request("http://d.10jqka.com.cn/v2/realhead/hs_" + id + "/last.js", self.infoParse,meta={'share_id': id})

处理公司详情页面
依旧是使用xpath解析结果，没啥说的

    def companyParse(self, response):
        # print('companyParsestart')
        # response.xpath("//div[@stat][@id='detail']//table[@class='m_table']/@class").extract()
        root = response.xpath("//div[@class='content page_event_content']")[0]
        name = root.xpath("//div[@stat][@id='detail']//table[@class='m_table']//tr[1]//td[2]//span/text()")[0].extract()
        start_time = root.xpath("//div[@stat][@id='publish']//table[@class='m_table']//tr[1]//td[1]//span/text()")[
            0].extract()
        market_time = root.xpath("//div[@stat][@id='publish']//table[@class='m_table']//tr[2]//td[1]//span/text()")[
            0].extract()
        print("这是公司详情页 公司全称", name, '成立时间', start_time, '上市时间', market_time)
        company = Company()
        company['share_id'] = response.meta['share_id']
        company['name'] = name
        company['start_time'] = start_time
        company['market_time'] = market_time
        yield company

        # print('cpmpanyParse end')

财务详情页 依然是xpath

    def financeParse(self, response):
        # print('financeParse start')
        print("财务详情页 ", "公司ID", response.meta['share_id'], "总营收")
        jsonStr = response.xpath("//p[@id='main']/text()").extract()[0]
        # 按年划分
        finance = json.loads(jsonStr)['year']

        # print(json.dumps(finance[0]))
        # print(json.dumps(finance[6]))
        company = Company()
        company['share_id'] = response.meta['share_id']
        company['year'] = finance[0]
        company['revenue'] = finance[6]
        yield company
        # print('financeParse end')


这里使用的是接口，所以返回的结果需要使用json.loads转化为json结构

    def infoParse(self, response):
        # print('infoParse start')
        market_value = json.loads(str(response.body)[41:-2])['items']['3541450']
        print("公司信息接口 ", "公司ID", response.meta['share_id'], "总市值", market_value)
        company = Company()
        company['share_id'] = response.meta['share_id']
        company['market_value'] = market_value
        yield company

        # print('infoParse end')


##使用[Pipeline](https://scrapy-chs.readthedocs.io/zh_CN/1.0/topics/item-pipeline.html)处理
pipeline的使用方法参考链接，以股票代码作为唯一值，更新数据库

[项目地址](https://github.com/Billxxxx/TongHuaShunSpider)
待优化：
+ 扒下来的网页要保存在本地，以便后续使用
+ 使用代理池，实现多线程爬取，优化速度
+ 控制台
