#!/usr/bin/env python
# encoding: utf-8
import sys
import json
import random

import re
import jieba

word_list = ['QQ', 'Q群', '666', '444', '操你', '艹你', '代打', '加攻击', '加攻', '加Q', '加QQ', '加V', '加微信', '加微', '加扣', '扣扣', '加我', 'www.', 'Q币', '河南人', '死全家', 'QQ群', '联系QQ', '联系Q']
for w in word_list:
    jieba.add_word(w)


from tgrocery import Grocery

def is_contain_chinese(check_str):
    for ch in check_str.decode('utf-8'):
        if u'\u4e00' <= ch <= u'\u9fff':
            return True
    return False

def my_tokenize(text):
    return jieba.cut(text.strip(), cut_all=True, HMM=True)

punct = set(u''':!),.:;?]}¢'"、。〉》」』】〕〗〞︰︱︳﹐､﹒
﹔﹕﹖﹗﹚﹜﹞！），．：；？｜｝︴︶︸︺︼︾﹀﹂﹄﹏､～￠
々‖•·ˇˉ―--′’”([{£¥'"‵〈《「『【〔〖（［｛￡￥〝︵︷︹︻
︽︿﹁﹃﹙﹛﹝（。｛“‘-—_…''')
filterpunt = lambda s: ''.join(filter(lambda x: x not in punct, s))

re_get_han = re.compile("[A-Za-z0-9\[\`\~\!\@\#\$\^\&\*\(\)\=\|\{\}\'\:\;\'\,\[\]\.\<\>\/\?\~\！\@\#\\\&\*\%]")

#grocery = Grocery('sample', custom_tokenize=my_tokenize)
def train():
    grocery = Grocery('sample', custom_tokenize=my_tokenize)
    train_src = []
    spam_train_src = []
    ham_train_src = []
    # {"predict": {"politic": -0.28083912480127471, "spam": -0.32894105503504062, "porn": -0.22844261821606801, "nonsense": 1.3501367894308456, "ham": -0.51191399137917704}, "res": "nonsense"}
    nonsense_train_src = []
    porn_train_src = []
    politic_train_src = []
    ad_train_src = []
    c = 0
    for i in open('./shumei_spam.out'):
        line = i.split(' ')
        if not is_contain_chinese(i.strip('\n')): continue
        #if len(line) < 3: continue
        spam_train_src.append((line[0], line[1].strip('\n')))
        c += 1

    for i in open('./daguan.out'):
        try:
            d = json.loads(i.strip('\n'))
        except:
            continue
        if not is_contain_chinese(d['text'].encode('utf8')) and (not d['text'].strip('\n').isdigit()): continue
        if ('weight_nonsense' not in d) or ('politic' not in d) or ('porn' not in d) or ('weight_ad' not in d) or ('reaction' not in d): continue

        if d['weight_ad'] >  0.1:
            ad_train_src.append(('ad', d['text']))
        elif d['porn'] >  0.3:
            porn_train_src.append(('porn', d['text']))
        elif d['weight_nonsense'] > 0.4:
            nonsense_train_src.append(('nonsense', d['text']))
        elif d['politic'] >  0.1:
            politic_train_src.append(('politic', d['text']))
        elif d['reaction'] >  0.1:
            politic_train_src.append(('politic', d['text']))
        else:
            ham_train_src.append(('ham', d['text']))



    #train_src = []
    ##total_count = len(spam_train_src) + len(ham_train_src) + len(nonsense_train_src) + len(politic_train_src) + len(porn_train_src) + len(train_src)
    print 'spam len:', len(spam_train_src), 'ham len:', len(ham_train_src), 'nonsense len:', len(nonsense_train_src), 'politic len:', len(politic_train_src), 'porn len:', len(porn_train_src)
    train_src.extend(ad_train_src)
    train_src.extend(spam_train_src)
    train_src.extend(ham_train_src)
    train_src.extend(nonsense_train_src)
    train_src.extend(politic_train_src)
    train_src.extend(porn_train_src)
    #total_count = len(train_src)

    #random.shuffle(spam_train_src)
    #random.shuffle(ham_train_src)
    #random.shuffle(nonsense_train_src)
    #random.shuffle(politic_train_src)
    #random.shuffle(porn_train_src)
    random.shuffle(train_src)


    grocery.train(train_src[:-5000])
    #grocery.train('chinese_ham/msg.text')
    grocery.save()
    test_src = train_src[-1000:]
    print grocery.test(test_src)

new_grocery = Grocery('sample')

def load_grocery():
    global new_grocery
    new_grocery.load()


import os
import json
import platform

import tornado
import tornado.web
import tornado.wsgi
import tornado.options
import tornado.httpserver
#import tornado.autoreload
import tornado.ioloop



class MainHandler(tornado.web.RequestHandler):
    def get(self):
        msg = self.get_argument('msg')
        #msg1 = re.sub(re_get_han, '', msg)
        #msg2 = filterpunt(msg)
        #ret1 = new_grocery.predict(msg1)
        #ret2 = new_grocery.predict(msg2)
        ret = new_grocery.predict(msg)
        manual_prediction = None

        if ret.dec_values['politic'] > 0:
            manual_prediction = 'politic'
        elif ret.predicted_y == 'spam':
            if ret.dec_values['spam'] - ret.dec_values['ham'] < 0.1:
                manual_prediction = 'ham'
            if (ret.dec_values['spam'] < 0.3 ) and (ret.dec_values['spam'] - ret.dec_values['porn'] < 0.2 or ret.dec_values['spam'] - ret.dec_values['nonsense'] < 0.3):
                manual_prediction = 'nonsense'
        elif ret.dec_values['porn'] > 0.5:
            manual_prediction = 'porn'
        elif ret.predicted_y == 'nonsense':
            if ret.dec_values['nonsense'] - ret.dec_values['spam'] < 0.2 and ret.dec_values['spam'] > 0.3:
                manual_prediction = 'spam'
            elif ret.dec_values['spam'] + ret.dec_values['ad'] > 0.3:
                manual_prediction = 'spam'
        elif ret.dec_values['spam'] > 0 and ret.dec_values['ad'] > 0:
            manual_prediction = 'spam'
        elif ret.dec_values['ad'] > 0.3:
            manual_prediction = 'ad'

        #ret = ret1
        #if ret1.predicted_y != ret2.predicted_y:
        #    print 'use ret2 as res'
        #    print 'ret1:', ret1.dec_values, 'ret2:', ret2.dec_values
        #    ret = ret2
        #print new_grocery.get_load_status()
        #print ret.dec_values
        return self.finish(json.dumps({'res': manual_prediction or ret.predicted_y, 'predict': ret.dec_values}))

handlers = [
    (r"/v1/classify", MainHandler),
]

settings = dict(
        cookie_secret="y+iqu2psQRyVqvC0UQDB+iDnfI5g3E5Yivpm62TDmUU=",
        debug=True,
        session_secret='terminus',
        session_dir='sessions',
        template_path=os.path.join(os.path.dirname(__file__), "templates"),
        static_path=os.path.join(os.path.dirname(__file__), "static"),
        xsrf_cookies=False,
)


class Application(tornado.web.Application):
    def __init__(self):
        tornado.web.Application.__init__(self, handlers, **settings)
        # self.session_manager = session.TornadoSessionManager(settings["session_secret"], settings["session_dir"])
        # self.db = dbutils.Connection(
        #    host=options.DATABASE_HOST, database=options.DATABASE_NAME,
        #    user=options.DATABASE_USER, password=options.DATABASE_PASSWORD)



def main(port):
    #train()
    load_grocery()
    tornado.options.parse_command_line()
    print "start on port %s..." % port
    http_server = tornado.httpserver.HTTPServer(Application(), xheaders=True)
    http_server.listen(port)
    #tornado.autoreload.start()
    tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
    main(8080)
