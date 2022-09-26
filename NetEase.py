import sys
import requests
import json
import base64
from Crypto.Cipher import AES
from enum import Enum

# windows中文乱码使用
# import io
#
# sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='gb18030')

second_param = "010001"
third_param = "00e0b509f6259df8642dbc35662901477df22677ec152b5ff68ace615bb7b725152b3ab17a876aea8a5aa76d2e417629ec4ee341f56135fccf695280104e0312ecbda92557c93870114af6c9d05c4f7f0c3685b7a46bee255932575cce10b424d813cfe4875d3e82047b97ddef52741d546b8e289dc6935b3ece0462db0a22b8e7 "
forth_param = "0CoJUm6Qyw8W8jud"

csrf_token = ""
req_headers = {
                'Cookie': r'MUSIC_U=;',
                'Referer': 'https://music.163.com/'
            }


class ParamType(Enum):
    Search = 0
    Recommend = 1
    Song = 2
    Tracks = 3



class SongInfo:
    def __init__(self, song):
        self.id = song['id']
        self.name = song['name']
        self.fee = song['fee']
        self.reason = ''
        if 'reason' in song:
            self.reason = str(song['reason'])

        self.artists = []
        if 'artists' in song:
            _artists = song['artists']
        else:
            _artists = song['ar']
        for _a in _artists:
            self.artists.append(_a['name'])

        if 'album' in song:
            _album = song['album']
        else:
            _album = song['al']
        self.album = _album['name']
        self.picUrl = _album['picUrl']
        self.level = song['privilege']['playMaxBrLevel']
        # self.url = get_song(str(self.id))


def req_search(_word, index):
    req_url = 'https://music.163.com/weapi/cloudsearch/get/web?csrf_token='
    params = get_params(_word, ParamType.Search)
    encSecKey = get_encSecKey()
    req_data = {
        'params': params,
        'encSecKey': encSecKey
    }
    resp = requests.post(req_url, headers=req_headers, data=req_data)
    # resp = requests.get(f'https://music.cyrilstudio.top/search?keywords={word}')
    result = resp.text

    data = json.loads(result)
    code = data['code']
    index = int(index)

    if code == 200:
        songs = data['result']['songs']
        songList = []
        for song in songs:
            songInfo = SongInfo(song=song)
            songList.append(songInfo)
        return songList

    return None


def req_recommend():
    url = 'https://music.163.com/weapi/v2/discovery/recommend/songs?csrf_token='
    
    params = get_params('', ParamType.Recommend)
    encSecKey = get_encSecKey()
    req_data = {
        'params': params,
        'encSecKey': encSecKey
    }
    resp = requests.post(url, headers=req_headers, data=req_data)
    result = resp.text
    
    data = json.loads(result)
    code = data['code']

    if code == 200:
        songs = data['recommend']
        songList = []
        for song in songs:
            songInfo = SongInfo(song=song)
            songList.append(songInfo)
        return songList

    return None


def get_song(_id):
    url = 'https://music.163.com/weapi/song/enhance/player/url/v1?csrf_token='
    
    params = get_params(_id, ParamType.Song)
    encSecKey = get_encSecKey()
    req_data = {
        'params': params,
        'encSecKey': encSecKey
    }
    resp = requests.post(url, headers=req_headers, data=req_data)
    result = resp.text
    
    data = json.loads(result)
    code = data['code']
    if code == 200:
        songs = data['data']
        song = songs[0]['url']
        return song

    return None


def req_tracks(_id):
    url = 'https://music.163.com/weapi/playlist/manipulate/tracks?csrf_token='
    
    params = get_params(_id, ParamType.Tracks, 'add')
    encSecKey = get_encSecKey()
    req_data = {
        'params': params,
        'encSecKey': encSecKey
    }
    resp = requests.post(url, headers=req_headers, data=req_data)
    result = resp.text
    
    data = json.loads(result)
    code = data['code']
    if code == 200:
        return '添加成功!'
    elif 'message' in data:
        return data['message']
    return '添加失败'


def AES_encrypt(text, key, iv):
    # print(text)
    text = text.encode('utf-8')
    pad = 16 - len(text) % 16
    text = text + (pad * chr(pad)).encode('utf-8')  # 需要转成二进制，且可以被16整除
    key = key.encode('utf-8')
    iv = iv.encode('utf-8')
    encryptor = AES.new(key, AES.MODE_CBC, iv)
    encrypt_text = encryptor.encrypt(text)  # .encode('utf-8')
    encrypt_text = base64.b64encode(encrypt_text)
    return encrypt_text.decode('utf-8')


def get_encSecKey():
    encSecKey = "257348aecb5e556c066de214e531faadd1c55d814f9be95fd06d6bff9f4c7a41f831f6394d5a3fd2e3881736d94a02ca919d952872e7d0a50ebfa1769a7a62d512f5f1ca21aec60bc3819a9c3ffca5eca9a0dba6d6f7249b06f5965ecfff3695b54e1c28f3f624750ed39e7de08fc8493242e26dbc4484a01c76f739e135637c"
    return encSecKey


def get_params(_word, paramType, tracks_param='add'):  # 获取params 参数的函数
    iv = "0102030405060708"
    first_key = forth_param
    second_key = 16 * 'F'
    _param = ''
    if paramType == ParamType.Recommend:
        _param = get_recommend_param()
    elif paramType == ParamType.Song:
        _param = get_song_param(_word)
    elif paramType == ParamType.Search:
        _param = get_search_param(_word)
    elif paramType == ParamType.Tracks:
        _param = get_track_param(_word, tracks_param)

    h_encText = AES_encrypt(_param, first_key, iv)
    h_encText = AES_encrypt(h_encText, second_key, iv)
    return h_encText


def get_search_param(_word):
    _param = r'{"hlpretag":"<span class=\"s-fc7\">","hlposttag":"</span>","s":"' + _word + '","type":"1","offset":"0","total":"true","limit":"30","csrf_token":""}'
    return _param


def get_recommend_param():
    _param = r'{"offset":"0","total":"true","csrf_token":""}'
    return _param


def get_song_param(_id):
    _param = r'{"ids":"[' + _id + ']","level":"hires","encodeType":"mp3","csrf_token":""}'   # level: standard higher exhigh lossless hires
    return _param


def get_track_param(_id, _op):
    _param = r'{"tracks":"[object Object]","pid":"5862739","trackIds":"['+_id+']","op":"'+_op+'","csrf_token":""}'
    return _param


def echo_html(_list, _word):
    html_style = '''body{
                            margin:0px;
                            background-color:#333;
                            word-wrap: break-word;
                            word-break: break-word;
                        }
                        .top{
                            position:fixed;
                            top:0;
                            width:100%;
                            height:80px;
                            z-index:1;
                            background-color:#333;
                            /*filter:drop-shadow(0px 1px 3px rgba(220,50,0,0.3));*/
                        }
                        .content{
                            padding:0px;
                            margin:15px;
                            margin-top:100px;
                            margin-bottom:50px;
                        }
                        .item{
                            margin:10px;
                        }
                        .music-group{
                            display:grid;
                            grid-template-columns: 30px 1fr 50px;
                            /*filter:drop-shadow(0px 8px 5px rgba(220,50,0,0.3));*/
                        }
                        .left{
                            height:50px;
                            display:flex;
                            background-color:#C10D0C;
                        }
                        .music{
                            background-color:#505050;
                            border-radius:0px;
                            height:50px;
                        }
                        .music-name{
                            height:30px;
                        }
                        .album{
                            width:50px;
                            height:50px;
                            filter:blur(0.3px);
                            background-color:#C10D0C;
                        }
                        .font10{
                            font-size:10px;
                        }
                        .play{
                            display:flex;
                            width:50px;
                            height:50px;
                            cursor: pointer;
                        }
                        .play-icon{
                            width: 17px;
                            height: 17px;
                            margin-left:-32px;
                            margin-top:15px;
                            content:url(/images/play.png);
                            z-index:1;
                            filter:drop-shadow(0px 0px 3px #303030);
                        }
                        .right{
                            display:flex;
                            align-items:center;
                            background-color:#BDB76B;
                        }
                        .center{
                            display:flex;
                            text-align:center;
                            justify-content:center;
                            align-items:center;
                        }
                        .text{
                            color:#ccc;
                        }
                        .playing{
                            color:#C10D0C;
                            cursor: pointer;
                        }
                        .title{
                            color:#ccc;
                            margin:10px;
                            height:60px;
                            display:flex;
                        }
                        .bgImg{
                            background: url(/images/table.png) no-repeat 0 9999px;
                        }
                        .inline{
                            display:inline;
                        }
                    '''
    html_script = '''$(function(){
                        var music = document.getElementById("music");
                    })
                    $(window).scroll(function(){
                        if($(window).scrollTop()>10){
                            $(".top").css("filter", "drop-shadow(0px 1px 3px rgba(220,50,0,0.3))");
                        }
                        else{
                            $(".top").css("filter", "none");
                        }
                    });
                    function onClick(data){
                        music.pause();
                        var id = data.getAttribute("data-id");
                        var title = data.getAttribute("data-title");
                        $(".title").height(30);
                        $.get("/python/music-url"+id,function(data,status){
                            music.src=data;
                            music.play();
                            var playing = document.getElementsByClassName("playing")[0];
                            playing.innerHTML = "正在播放: "+title;
                        });
                    }
                    function toggleMusic(){
                        if(music.paused){
                            music.play();
                        }
                        else{
                            music.pause();
                        }
                    }
                '''
    html_head = f'<head>\
                <meta name="viewport" content="width=device-width,initial-scale=1,user-scalable=0">\
                <script src="/javascripts/jquery.min.js"></script>\
                <title>{_word}</title><style>{html_style}</style><script>{html_script}</script></head>'
    html = html_head + f'<div class="top"><div class="title center">{_word}</div>\
                    <div class="playing center" onclick="toggleMusic()"></div><audio id="music"></audio></div>\
                    <div class="content">'
    song_index = 0
    for song in _list:
        song_index += 1
        _artists = ' / '.join(song.artists)
        html += f'<div class="item">\
                    <div class="music-group">\
                    <div class="left text center">{song_index}</div>\
                    <div class="music text">\
                        <div class="music-name center">{song.name} - {_artists}</div>\
                        <div class="album-text font10 center">({song.album})</div>\
                    </div>\
                    <div class="right">\
                    <a class="play" onclick="onClick(this)" data-title="{song_index}.{song.name} - {_artists}"\
                     data-id="{song.id}" title="播放"><img class="album" src="{song.picUrl}"><img class="play-icon"></a>\
                     \
                     </div>\
                    </div>\
                    <div class="reason inline text font10">{song.reason}</div>\
                </div>'
    print(html + '</div>')


def echo_search():
    search_index = 0
    word = '二十岁的某一天'

    if len(sys.argv) > 1:
        word = sys.argv[1]
        if word.startswith('url'):
            _id = word.split('url')[1]
            print(get_song(_id))
            return
        elif len(sys.argv) > 2:
            search_index = sys.argv[2]

    songList = req_search(word, search_index)

    if songList:
        echo_html(songList, word)
    else:
        print(f'未找到!')


def echo_recommend():
    songList = req_recommend()
    if songList:
        echo_html(songList, '每日歌曲推荐')
    else:
        print(f'未找到!')


if __name__ == '__main__':
    if len(sys.argv) > 1:
        echo_search()
    else:
        echo_recommend()
        # print(get_song('168087'))
