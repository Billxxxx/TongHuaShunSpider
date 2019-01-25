import scrapy
import json
from scrapy_splash import SplashRequest

from shares_data.items import Company

rank_base_page = 'http://q.10jqka.com.cn/index/index/board/all/field/zdf/order/desc/page/'


class DmozSpider(scrapy.Spider):
    name = "share_main"
    allowed_domains = [
        "q.10jqka.com.cn",
        "stockpage.10jqka.com.cn",
        "basic.10jqka.com.cn",
        "d.10jqka.com.cn"]
    start_urls = [
        # 不需要异步的页面
        rank_base_page + "1",
        # "http://basic.10jqka.com.cn/600157/company.html"  # 公司全称
        # "http://basic.10jqka.com.cn/600157/finance.html"  # 总营收
        # "http://d.10jqka.com.cn/v2/realhead/hs_600157/last.js"  # 总市值 成立时间 上市时间
    ]

    # def start_requests(self):
    #     yield SplashRequest(self.start_urls[0], self.parse,
    #                         args={'wait': 0.5}, )

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
            self.cpmpanyParse(response)
        elif "finance.html" in response.url:
            # print("这是finance详情页面")
            self.financeParse(response)
        elif "d.10jqka.com.cn/v2/realhead" in response.url:
            # print("这是realhead详情页面")
            self.infoParse(response)

    def handlePage(self, response):
        print("处理列表页面")
        trs = response.xpath("//tr")
        for tr in trs[1:]:
            # 股票代码 简称
            a = tr.xpath(".//a[@target='_blank']")
            name = tr.xpath(".//a[@target='_blank']")[1].xpath('text()').extract()[0]

            id = a[0].xpath('text()').extract()[0]
            # url = a[0].xpath('@href').extract()[0]
            # print(id, name)
            company = Company()
            company['share_id'] = id
            company['nick_name'] = name
            yield company

            # urls = response.xpath("//tr//a[@target='_blank']/@href").extract()
            # for url in urls:
            #     print(url)
            yield scrapy.Request("http://basic.10jqka.com.cn/" + id + "/company.html", self.cpmpanyParse,
                                 meta={'share_id': id})
            yield scrapy.Request("http://basic.10jqka.com.cn/" + id + "/finance.html", self.financeParse,
                                 meta={'share_id': id})
            yield scrapy.Request("http://d.10jqka.com.cn/v2/realhead/hs_" + id + "/last.js", self.infoParse,
                                 meta={'share_id': id})

    def cpmpanyParse(self, response):
        # print('cpmpanyParse start')
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

    def infoParse(self, response):
        # print('infoParse start')
        market_value = json.loads(str(response.body)[41:-2])['items']['3541450']
        print("公司信息接口 ", "公司ID", response.meta['share_id'], "总市值", market_value)
        company = Company()
        company['share_id'] = response.meta['share_id']
        company['market_value'] = market_value
        yield company

        # print('infoParse end')