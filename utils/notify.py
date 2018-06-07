# -*- coding: utf-8 -*-
from __future__ import print_function
from __future__ import unicode_literals

import sys
from smtplib import SMTP

from .log import LOG
from .conf import Config

class Notify(object):
    def __init__(self, msg, dst, sender=None, **kwargs):
        self.dst = dst
        self.msg = msg
        self.sender = sender
        self.kwargs = kwargs
        self.result = None

    def do(self):
        try:
            r = self.notify()
        except:
            r = None
            self.result = 1
            err = sys.exc_info()
            LOG.error("fail notify: " + self.__class__.__name__ )
            LOG.error("{err}".format(err=err[1]))
        else:
            self.result = 0
            LOG.info("do notify: " + self.__class__.__name__)
        finally:
            return r

    def notify(self):
        raise Exception("not implemented yet")


class EmailNotify(Notify):
    SENDER = Config.EMAIL_SENDER
    DST = Config.EMAIL_DST

    def __init__(self, msg, dst=None, sender=None, **kwargs):
        Notify.__init__(self, msg, dst, sender, **kwargs)
        self.dst = EmailNotify.DST if self.dst is None else self.dst
        self.sender = EmailNotify.SENDER if self.sender is None else self.sender
        self.dst = self.dst if isinstance(self.dst, list) else [self.dst]

    @property
    def subject(self):
        return self.kwargs.get("subject", "auto notification")

    def notify(self):
        user, server = self.sender.split("@")
        smtp = "smtp." + server
        password = '12F5BD8aaa!@#' if self.sender == EmailNotify.SENDER else self.kwargs.get("password", "12F5BD8aaa!@#")

        mailb = self.msg if isinstance(self.msg, list) else [self.msg]
        mailh = ["From: {sender}".format(sender=self.sender), "To: {dst}".format(dst=", ".join(self.dst)), "Subject: "+self.subject]
        mailmsg = "\r\n\r\n".join(["\r\n".join(mailh), "\r\n".join(mailb)])
        send = SMTP(smtp)
        send.login(user, password)
        r = send.sendmail(self.sender, self.dst, mailmsg.encode("utf-8"))
        send.quit()
        LOG.debug(mailmsg)
        LOG.info("send email to: {dst}".format(dst=self.dst))
        # log.debug("result: {r}".format(r=r))
        return r

