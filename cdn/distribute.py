# -*- coding: utf-8 -*-
from __future__ import print_function
from __future__ import unicode_literals

from qiniu import Auth, put_file, etag, urlsafe_base64_encode
from qiniu import BucketManager, CdnManager

import oss2
# from oss2.c import md5_string
from aliyunsdkcore import client
from oss2.compat import to_string
from aliyunsdkcdn.request.v20141111 import RefreshObjectCachesRequest, PushObjectCacheRequest
import os
import sys
import argparse
import hashlib
import base64
sys.path.append("../")
from utils.log import get_logger
import logging
# import logging as log
log = get_logger("LOG_CDN", path="../logs/", level=logging.DEBUG, max_byte=1024*1024*50, backup_count=10)


class FileInfo(object):
    def __init__(self, parent, rpath, bucket, rname):  #rpath: , rname:
        """
        File information used for uploading
        :param parent: parent dir
        :param rpath:  relative path
        :param bucket: cdn bucket
        :param rname:  remote name in cdn(bucket)
        """
        self.parent = parent
        self.rpath = rpath
        self.bucket = bucket
        self.rname = rname
        self.size = os.path.getsize(rpath)

    def __str__(self):
        return "{self.parent} {self.rpath}: {self.bucket} {self.rname} {self.size}".format(self=self)


class AL_FileInfo(FileInfo):
    BLOCK_SIZE = 4 * 1024 * 1024   # same as qiniu.utils._BLOCK_SIZE

    def __init__(self, parent, rpath, bucket, rname):
        FileInfo.__init__(self, parent, rpath, bucket, rname)
        self.etag = etag(self.rpath)
        self.md5 = to_string(self.calculate_file_md5())
        self.crc = to_string(self.calculate_file_crc64())

    def calculate_file_crc64(self):
        """
        calculate file crc64 used for check
        :return:
        """
        with open(self.rpath, 'rb') as f:
            crc64 = oss2.utils.Crc64(0)
            while True:
                data = f.read(AL_FileInfo.BLOCK_SIZE)
                if not data:
                    break
                crc64.update(data)

        return crc64.crc

    def calculate_file_md5(self):
        """
        calculate file md5 used for check
        :return:
        """
        with open(self.rpath, 'rb') as f:
            md5 = hashlib.md5()
            while True:
                data = f.read(AL_FileInfo.BLOCK_SIZE)
                if not data:
                    break
                md5.update(data)

        return base64.b64encode(md5.digest())

    def __str__(self):
        return "Ali FileInfo: " + FileInfo.__str__(self) + " {self.etag}".format(self=self)


class QN_FileInfo(FileInfo):
    def __init__(self, parent, rpath, bucket, rname):
        FileInfo.__init__(self, parent, rpath, bucket, rname)
        self.etag = etag(self.rpath)

    def __str__(self):
        return "Qiniu FileInfo: " + FileInfo.__str__(self) + " {self.etag}".format(self=self)


class CDN(object):
    # set extensions
    ALLOW_EXTENSIONS = [".ts", ".mp4", ".m3u8", ".jpg", ".png", ".apk", ".7z", ".bin", ".yak", ".js", ".css", ".html"]

    def __init__(self, parentdirs, **kwargs):
        self.bucket = kwargs.get("bucket")
        self.sk = kwargs.get("sk")
        self.ak = kwargs.get("ak")
        self.refresh_uri = kwargs.get("refresh_uri")
        self.cdn_uri = kwargs.get("cdn_uri")

        if isinstance(parentdirs, str):
            self.parentdirs = [parentdirs]
        else:
            self.parentdirs = parentdirs
        for parent in self.parentdirs:
            if not os.path.exists(parent):
                raise Exception("{parent} not exist".format(parent=parent))
            if not os.path.isdir(parent):
                raise Exception("{parent} not a dir".format(parent=parent))
        self.kwargs = kwargs

        self.online_files = set()  # dic[bucket] = (f1, f2)
        self.local_files = set()  # dic[parent] = (f1, f2), files under parent directory

        self.new_files = set()  # (nf1, nf2, ...), file in local but not in CDN, or the two copies are different
        self.altered_files = set()
        self.old_files = set()  # (of1, of2, ...), file in local as well as CDN
        self.to_delete_files = set()
        self.upload_files = set()
        self.link_files = set()

    def do(self):
        try:
            self.get_local_files()
            self.get_online_files()
            self.analyze_files()
            self.display()
            self.delete_files()
            self.push_files()
        except Exception as e:
            log.error("Error when sychronize data to CDN")
            raise Exception("CDN do error {error}".format(error=str(e)))
        else:
            pass
        finally:
            pass

    def get_online_files(self):
        self._pull(self.bucket)
        # log.debug("online_files: {0}".format(self.online_files))   # to large

    def get_local_files(self):
        try:
            for parent in self.parentdirs:
                for rparent, dns, fns in os.walk(parent):  # rparent: relative parent
                    for fn in fns:
                        if self._filter_local_file(rparent, fn):
                            tmp = os.path.join(rparent, fn)
                            tmp = self.to_unicode(tmp)
                            self.local_files.add(tmp)
        except Exception as e:
            log.error("CDN:get_local_files error: {error}".format(error=str(e)))
            raise Exception("Distribute_CDN_get_local_files_error: {error}".format(error=str(e)))
        log.debug("local_files: {0}".format(self.local_files))

    def analyze_files(self):
        try:
            for fn in self.local_files:
                parent = None
                for tmp in self.parentdirs:
                    if fn.startswith(tmp):
                        parent = tmp
                        break
                r1 = fn[len(parent):]
                if r1.startswith("/"):
                    r1 = r1[1:]
                prefix = self.kwargs.get("prefix", None)
                if prefix is None:
                    tmp = r1
                else:
                    if prefix.startswith("/"):
                        prefix = prefix[1:]
                    tmp = os.path.join(prefix, r1)

                fi = self._set_file_info(parent, fn, self.bucket, tmp)
                # add url link file whether exist in cdn
                ext = os.path.splitext(fi.rname)[1]
                if ext in ['.mp4', '.m3u8', '.webm', '.mpd', '.apk', '.jpg', '.png', '.7z']:  # filter ts, dash
                    self.link_files.add(fi.rname)

                if self._filter_push_file(fi):
                    if fi.rname in self.online_files:
                        self.altered_files.add(fi)
                    else:
                        log.debug("add to new file: {fi}".format(fi=fi))
                        self.new_files.add(fi)
                else:
                    self.old_files.add(fi)

            for rname in self.online_files:
                if self._filter_delete_files(rname):
                    fi = FileInfo(None, None, self.bucket, rname)
                    self.to_delete_files.add(fi)

        except Exception as e:
            log.error("CDN:analyze_files error: {error}".format(error=str(e)))
            raise Exception("Distribute_CDN_analyze_files_error: {error}".format(error=str(e)))

    def push_files(self):
        try:
            log.info("File to relpace:")
            for fi in self.altered_files:
                self._push(fi)
                self._refresh(fi)
            log.info("New file to upload:")
            for fi in self.new_files:
                self._push(fi)
                self._prefetch(fi)
            if self.kwargs.get("overwrite"):
                for fi in self.old_files:
                    self._push(fi)
        except Exception as e:
            log.error("CDN:push_files error: {error}".format(error=str(e)))

            raise Exception("Distribute_CDN_push_files_error.{error}".format(error=str(e)))

    def delete_files(self):
        if not self.kwargs.get("delete"):
            return
        for fi in self.to_delete_files:
            self._delete_online_files(fi)

    def _filter_delete_files(self, rname):
            fb, fn = os.path.split(rname)
            if fn.startswith("."):
                return True

    def display(self):
        self._display(self.to_delete_files, tag="delete")
        self._display(self.old_files, tag="exist{replaced}".format(replaced= "(overwrite)" if self.kwargs.get("overwrite") else ""))
        self._display(self.altered_files, tag="replace")
        self._display(self.new_files, tag="new")

    def _display(self, setdata, tag):
        if len(setdata) == 0:
            log.debug("NO *{tag}* FILE".format(tag=tag))
        else:
            datas = sorted(setdata, key=lambda fi: fi.rname)
            for fi in datas:
                log.debug("{tag}: {fi}".format(tag=tag, fi=fi))

    def _delete_online_files(self, rname):
        raise NotImplementedError()

    def _filter_local_file(self, parent, rpath):
        fn = os.path.basename(rpath)
        if self.kwargs.get("file_prefix_filter") and not fn.startswith(self.kwargs.get("file_prefix_filter")):
                return False
        if fn.startswith(".") or fn.startswith("#") or " " in fn:
            log.warning("local file with illegal name: {fn}".format(fn=fn))
            return False
        ext = os.path.splitext(fn)[1]
        if ext in CDN.ALLOW_EXTENSIONS:
            return True
        else:
            log.warning("local file with illegal extension: {fn}".format(fn=fn))
            return False

    def _set_file_info(self, parent, rpath, bucket, rname):
        raise NotImplementedError()

    def _filter_push_file(self, fn):
        raise NotImplementedError()

    def _pull(self, bucket):
        """

        :param bucket:
        :return:
        """
        raise NotImplementedError()

    def _push(self, fi):
        """

        :param fi:<FileInfo>
        :return:
        """
        raise NotImplementedError()

    def _prefetch(self, fi):
        """
        预取资源到cdn节点
        :param fi: <FileInfo>
        :return:
        """
        raise NotImplementedError()

    def _refresh(self, fi):
        """
        刷新资源到cdn节点
        :param fi: <FileInfo>
        :return:
        """
        raise NotImplementedError()


    @staticmethod
    def to_unicode(s):
        if sys.version_info < (3, 0):
            return s.decode("utf-8")
        else:
            return s


class ALI(CDN):
    META = {'x-oss-meta-author': 'kandao'}

    def __init__(self, **kwargs):
        CDN.__init__(self, **kwargs)
        self.endpoint = kwargs.get("endpoint",)
        self.region_id = kwargs.get("region_id", "cn-shenzhen")
        self.auth = oss2.Auth(self.ak, self.sk)
        # if use cname, headobject return error
        # self.bucket_mgr = oss2.Bucket(self.auth, self.cdn_uri, self.bucket, is_cname=True)
        self.bucket_mgr = oss2.Bucket(self.auth, self.endpoint, self.bucket)
        self.old_etags = dict()  # md5
        self.client = client.AcsClient(ak=self.ak, secret=self.sk, region_id=self.region_id)

    def _pull(self, bucket):
        try:
            # eof = True
            # marker = None
            # while eof:
            #     if marker is not None:
            #         log.debug("more files on CDN")
            #     ret = self.bucket_mgr.list_objects(marker=marker, max_keys=500)
            #     marker = ret.next_marker
            #     eof = ret.is_truncated
            #     self._process_data(ret.object_list)

            for i, object_info in enumerate(oss2.ObjectIterator(self.bucket_mgr, max_keys=500, max_retries=3)):
                self._process_data(object_info)
        except Exception as e:
            log.error("QN:_pull error: {error}".format(error=str(e)))
            raise Exception("Distribute_ALI_pull_error: {error}".format(error=str(e)))

        log.info("{0} items on ALI CDN".format(len(self.online_files)))
        # raise

    def _process_data(self, object_info):
        """
        :param object_info: <oss2.models.SimplifiedObjectInfo>
        :return:
        """
        log.debug("{0} {1} {2}".format(object_info.key, object_info.etag, object_info.size))
        rname = object_info.key
        if rname == "":
            log.warning("illegal name: null")
            return
        result = self.bucket_mgr.head_object(rname)
        _etag = result.headers.get("x-oss-meta-etag", "")
        if _etag == "":  # file not upload by distribute.py, need filter
            log.warning("{0} not upload by distribute.py to set meta".format(rname))
            return
        self.online_files.add(rname)
        self.old_etags[rname] = _etag

    def _set_file_info(self, parent, rpath, bucket, rname):
        return AL_FileInfo(parent, rpath, bucket, rname)

    def _filter_push_file(self, fi):
        if fi.rname in self.old_etags:
            if self.kwargs.get("check_prefix_filter"):
                fb, fn = os.path.split(fi.rname)
                if fn.startswith(self.kwargs.get("check_prefix_filter")):
                    return not fi.etag == self.old_etags[fi.rname]
                else:
                    if self.kwargs.get("no_check_overwrite"):
                        return True
                    if self.kwargs.get("no_check_no_overwrite"):
                        return False
                    return False
            else:
                if self.kwargs.get("no_check_overwrite"):
                    return True
                if self.kwargs.get("no_check_no_overwrite"):
                    return False
                return not fi.etag == self.old_etags[fi.rname]
        return True

    def _push(self, fi):
        try:
            headers = ALI.META
            headers.update({"Content-Length": str(fi.size)})  # for cdn check
            headers.update({"Content-MD5": fi.md5})   # for cdn check
            headers.update({"x-oss-meta-etag": fi.etag})
            ret = oss2.resumable_upload(self.bucket_mgr, fi.rname, fi.rpath, store=oss2.ResumableStore(root='/tmp'),
                                        multipart_threshold=10 * 1024 * 1024, part_size=10 * 1024 * 1024,
                                        num_threads=4, headers=headers)
            if ret.status != 200:
                log.error("ALI:_push: {file} error".format(file=fi.rpath))
                raise Exception("ALI:_push: {file} error".format(file=fi.rpath))
            if ret.crc != fi.crc:   # local check
                log.error("ALI:_push check: {file} error".format(file=fi.rpath))
                raise Exception("ALI:_push check: {file} error".format(file=fi.rpath))
            log.info("{fi} distributed".format(fi=fi))
            self.upload_files.add(fi.rname)
        except Exception as e:
            log.error("ALI:_push error: {error}".format(error=str(e)))
            raise Exception("Distribute_ALI_push_error :{error}".format(error=str(e)))

    def _refresh(self, fi):
        try:
            request_ = RefreshObjectCachesRequest.RefreshObjectCachesRequest()
            request_.set_ObjectPath(os.path.join(self.cdn_uri, fi.rpath))
            log.info("test path = {0}".format(request_.get_ObjectPath()))
            result = self.client.do_action_with_exception(request_)
            log.info("ALI:_refresh success:{0}".format(result))
        except Exception as e:
            log.error("ALI:_refresh error: {error}".format(error=str(e)))
            raise Exception("Distribute_ALI_refresh_error :{error}".format(error=str(e)))

    def _prefetch(self, fi):
        try:
            request_ = RefreshObjectCachesRequest.RefreshObjectCachesRequest()
            request_.set_ObjectPath(os.path.join(self.cdn_uri, fi.rpath))
            log.info("test path = {0}".format(request_.get_ObjectPath()))
            result = self.client.do_action_with_exception(request_)
            log.info("ALI:_prefetch success:{0}".format(result))
        except Exception as e:
            log.error("ALI:_prefetch error: {error}".format(error=str(e)))
            raise Exception("Distribute_ALI_prefetch_error :{error}".format(error=str(e)))

    def _filter_delete_files(self, rname):
        fb, fn = os.path.split(rname)
        if self.kwargs.get("delete_filter_dir") and fb.startswith(self.kwargs.get("delete_filter_dir")):
            return True
        if self.kwargs.get("deletq"
                           "e_filter") and fn.startswith(self.kwargs.get("delete_filter")):
            return True
        if fn.startswith(".") or " " in fn or fb.startswith("/"):
            return True
        return False

    def _delete_online_files(self, fi):
        self.bucket_mgr.delete_object(fi.rname)
        log.info("{bucket} {rname} removed".format(bucket=self.bucket, rname=fi.rname))


class QN(CDN):
    def __init__(self, **kwargs):
        CDN.__init__(self, **kwargs)
        self.auth = Auth(self.ak, self.sk)
        self.bucket_mgr = BucketManager(self.auth)
        self.cdn_mgr = CdnManager(self.auth)
        self.old_etags = dict()

    def _pull(self, bucket):
        try:
            eof = False
            marker = None
            while not eof:
                if marker is not None:
                    log.debug("more files on CDN")
                ret, eof, info = self.bucket_mgr.list(bucket, prefix=None, marker=marker, limit=None, delimiter=None)
                marker = ret.get("marker")
                self._process_data(ret)
        except Exception as e:
            log.error("QN:_pull error: {error}".format(error=str(e)))
            raise Exception("Distribute_QN_pull_error: {error}".format(error=str(e)))
        log.debug("{d} items on QINIU CDN".format(d=len(self.old_etags)))

    def _process_data(self, ret):
        try:
            if ret.get("items") is None:
                return
            items = ret.get("items")
            for dic in items:
                rname = dic["key"]
                if rname == "":
                    log.warning("illegal name: null")
                    continue
                self.online_files.add(self.to_unicode(rname))
                self.old_etags[rname] = dic["hash"]
        except Exception as e:
            log.error("QN:_process_data error: {error}".format(error=str(e)))
            raise Exception("Distribute_QN_process_data_error: {error}".format(error=str(e)))

    def _set_file_info(self, parent, rpath, bucket, rname):
        return QN_FileInfo(parent, rpath, bucket, rname)

    def _filter_push_file(self, fi):
        # log.debug("filter_push_file {fi}".format(fi=fi))
        if fi.rname in self.old_etags:
            if self.kwargs.get("check_prefix_filter"):
                fb, fn = os.path.split(fi.rname)
                if fn.startswith(self.kwargs.get("check_prefix_filter")):
                    return not fi.etag == self.old_etags[fi.rname]
                else:
                    if self.kwargs.get("no_check_overwrite"):
                        return True
                    if self.kwargs.get("no_check_no_overwrite"):
                        return False
                    return False
            else:
                if self.kwargs.get("no_check_overwrite"):
                    return True
                if self.kwargs.get("no_check_no_overwrite"):
                    return False
                return not fi.etag == self.old_etags[fi.rname]
        return True

    def _push(self, fi):
        try:
            token = self.auth.upload_token(fi.bucket, fi.rname, 7200)
            ret, info = put_file(token, fi.rname, fi.rpath, check_crc=True)
            log.debug("{ret} check".format(ret=ret, info=info))
            if ret is None:
                log.error("QN:_push: {file} error".format(file=fi.rpath))
                raise Exception("QN:_push: {file} error".format(file=fi.rpath))
            if ret["key"] != fi.rname or ret["hash"] != fi.etag:
                log.error("QN:_push check: {file} error".format(file=fi.rpath))
                raise Exception("QN:_push check: {file} error".format(file=fi.rpath))
            log.info("{fi} distributed".format(fi=fi))
            self.upload_files.add(fi.rname)
        except Exception as e:
            log.error("QN:_push error: {error}".format(error=str(e)))
            raise Exception("Distribute_QN_push_error :{error}".format(error=str(e)))

    def _refresh(self, fi):
        try:
            urls = [os.path.join(self.cdn_uri, fi.rpath)]
            ret, info = self.cdn_mgr.refresh_urls(urls)
            if ret["code"] == 200:
                log.info("QN:_refresh success:{0}--{1}".format(ret["urlSurplusDay"], ret["requestId"]))
            else:
                log.warn("QN:_refresh failed:{0}--{1}".format(ret["code"], ret["error"]))
        except Exception as e:
            log.error("QN:_refresh error: {error}".format(error=str(e)))
            raise Exception("Distribute_QN_refresh_error :{error}".format(error=str(e)))

    def _prefetch(self, fi):
        try:
            urls = [os.path.join(self.cdn_uri, fi.rpath)]
            ret, info = self.cdn_mgr.prefetch_urls(urls)
            if ret["code"] == 200:
                log.info("QN:_prefetch success:{0}--{1}".format(ret["urlSurplusDay"], ret["requestId"]))
            else:
                log.warn("QN:_prefetch failed:{0}--{1}".format(ret["code"], ret["error"]))
        except Exception as e:
            log.error("QN:_prefetch error: {error}".format(error=str(e)))
            raise Exception("Distribute_QN_prefetch_error :{error}".format(error=str(e)))

    def _filter_delete_files(self, rname):
        fb, fn = os.path.split(rname)
        if self.kwargs.get("delete_filter_dir") and fb.startswith(self.kwargs.get("delete_filter_dir")):
            return True
        if self.kwargs.get("delete_filter") and fn.startswith(self.kwargs.get("delete_filter")):
            return True
        if fn.startswith(".") or " " in fn or fb.startswith("/"):
            return True
        return False

    def _delete_online_files(self, fi):
        self.bucket_mgr.delete(self.bucket, fi.rname)
        log.info("{bucket} {rname} removed".format(bucket=self.bucket, rname=fi.rname))
        pass



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="compare the local files and remote files on name and hashing, "
                                                 "then push new files and overwrite file with different hashing")
    parser.add_argument("-p", "--path", nargs="*", default=["/data/HLS", "/data/MP4", "/data/WEBM"], help="local path")
    parser.add_argument("-b", "--bucket", nargs="?", default="webmirror", help="dst bucket")
    parser.add_argument("--prefix", nargs="?", default=None,
                        help="name prefix appending to the beginning of files to CDN")
    parser.add_argument("--overwrite", default=False, action="store_true",
                        help="overwrite existing files with same name and hash on CDN")
    parser.add_argument("--delete", dest="delete", default=False, action="store_true",
                        help="delete the illegal files on CDN")
    parser.add_argument("--no-push", dest="push", default=True, action="store_false",
                        help="not push local files to CDN")
    parser.add_argument("--dry-run", dest="dry_run", default=False, action="store_true",
                        help="do not run delete or push files")
    parser.add_argument("--no-check-overwrite", dest="no_check_overwrite", default=False, action="store_true",
                        help="not check hash and push file with same file name")
    parser.add_argument("--no-check-no-overwrite", dest="no_check_no_overwrite", default=False, action="store_true",
                        help="not check hash and not push file with same file name, depressed when --no-check-push set")
    parser.add_argument("--no-check", dest="no_check_no_overwrite", default=False, action="store_true",
                        help="not check hash and not push file with same file name, depressed when --no-check-push set")
    parser.add_argument("--check-filter", dest="check_prefix_filter", default=None,
                        help="check hash of files with specific name prefix")
    parser.add_argument("--file-filter", dest="file_prefix_filter", default=None,
                        help="filter files with specific name prefix")
    parser.add_argument("--delete-filter", dest="delete_filter", default=None,
                        help="filter delete files withe specific name prefix")
    parser.add_argument("--delete-filter-dir", dest="delete_filter_dir", default=None,
                        help="filter delete files with spcific dir prefix")
    args = parser.parse_args()
    if args.dry_run:
        args.delete = False
        args.push = False

    dic = vars(args)
    # for key in dic:
    #     dic[key] = CDN.to_unicode(dic[key])
    print(dic)
    # test = dict()
    # from cdn.local_settings import QINIU_AK, QINIU_SK
    # test["ak"] = QINIU_AK
    # test["sk"] = QINIU_SK
    # test["cdn_uri"] = "http://v1.kandaovr.com"
    # test["refresh_uri"] = "http://fusion.qiniuapi.com/v2/tune/refresh"
    # test["bucket"] = "rmstest"
    # qn = QN(parentdirs="examples", **test)
    # # parent = args.path
    # # bucket = args.bucket
    # qn.do()
    # print(qn.upload_files)

    test = dict()
    from cdn.local_settings import ALI_AK, ALI_SK
    test["ak"] = ALI_AK
    test["sk"] = ALI_SK
    test["cdn_uri"] = "http://kandao.info"
    test["refresh_uri"] = "http://fusion.qiniuapi.com/v2/tune/refresh"
    test["bucket"] = "kandaotest"
    test["endpoint"] = "oss-cn-shenzhen.aliyuncs.com"
    test["region_id"] = "cn-shenzhen"
    ali = ALI(parentdirs="resource", **test)
    # parent = args.path
    # bucket = args.bucket
    ali.do()
    print(ali.upload_files)

