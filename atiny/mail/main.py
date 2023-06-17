import traceback
import poplib

from collections import defaultdict
from typing import Union
from email.parser import Parser
from email.header import decode_header
from email.utils import parseaddr


from config import settings, secrets

try:
    from log import logger, log_stack
except ImportError:
    from ..log import logger, log_stack

from ..http.proxy import Proxy

from .proxy import proxify, POP3, POP3_SSL


class FastReturn(Exception):
    pass


class MailRet:

    def __init__(self, ok=False, log=None, data=None, mails=None, info=None):
        self.ok = ok
        self.log = log
        self.data = data
        self.mails = mails
        self.info = info


class MyPopClass:

    proxy: Union[None, Proxy]

    charsets = defaultdict(lambda: 'utf8', {
        '"Windows-1251"': 'cp1251',
        'Windows-1251': 'cp1251',
        'windows-1251': 'cp1251',
        '"windows-1251"': 'cp1251',
        'utf-8': 'utf8',
        '"utf-8"': 'utf8',
        'utf-8; format=flowed': 'utf8',

    })

    pop_auth: str
    pop_host: str

    def __init__(
            self, email, password,
            ssl=True, port=None,
            proxy=None, tmp_dir='.tmp'
    ):

        try:
            self.debug = settings.log.mail.debug
        except Exception:
            self.debug = False

        self.mails_ids = set()
        self.log_data = list()
        self.mails = list()

        self.tmp_dir = tmp_dir
        self.ssl = ssl
        if port:
            self.pop_port = str(port)
        else:
            if self.ssl:
                self.pop_port = '995'
            else:
                self.pop_port = None

        self.pop_email = email
        self.pop_password = password
        self.pop_user = self.pop_email.split('@')[0]
        self.mail_host = self.pop_email.split('@')[1]

        self.get_host()
        self.proxy_detect(proxy)

    def proxy_detect(self, proxy=None):
        try:
            if not proxy:
                proxy = secrets.proxy.mail
            self.proxy = Proxy(proxy)
        except Exception:
            self.proxy = None

    def log_return(self):
        return '\n'.join(self.log_data)

    def log(self, text):
        if self.debug:
            logger.info(text)

        self.log_data.append(text)
        return

    def log_bad(self, data=None):

        if data.get('need_verify'):
            file_with_mails = f'{self.tmp_dir}/bad_mails_needverify.txt'
        elif data.get('pwd'):
            file_with_mails = f'{self.tmp_dir}/bad_mails_password.txt'
        else:
            file_with_mails = f'{self.tmp_dir}/bad_mails_other.txt'

        try:
            with open(file_with_mails, 'a') as fi:
                fi.write(f'{self.pop_email}:{self.pop_password}\
                |{str(data.get("need_verify"))}|{str(data.get("resp"))}\n')
        except Exception:
            log_stack.error('log_bad.exception')

    def guess_charset(self, msg):
        # get charset from message object.
        charset = msg.get_charset()
        # if it can not get charset
        if charset is None:
            # get message header content-type value and retrieve
            # the charset from the value.
            content_type = msg.get('Content-Type', '').lower()
            pos = content_type.find('charset=')
            if pos >= 0:
                charset = content_type[pos + 8:].strip()

        return self.charsets[charset]

    def decode_str(self, s):
        value, charset = decode_header(s)[0]
        if charset:
            value = value.decode(charset)
        return value

    # variable indent_number is used to decide number of indent
    # of each level in the mail multiple bory part.
    def print_info(self, msg, indent_number=0):
        content = ''
        if indent_number == 0:
            # loop to retrieve from, to, subject from email header.
            for header in ['From', 'To', 'Subject']:
                # get header value
                value = msg.get(header, '')
                if value:
                    # for subject header.
                    if header == 'Subject':
                        # decode the subject value
                        value = self.decode_str(value)
                    # for from and to header.
                    else:
                        # parse email address
                        hdr, addr = parseaddr(value)
                        # decode the name value.
                        name = self.decode_str(hdr)
                        value = u'%s <%s>' % (name, addr)

                if self.debug:
                    logger.info(
                        'header: %s%s: %s' % (' ' * indent_number, header, value)
                    )

        # if message has multiple part.
        if msg.is_multipart():
            # get multiple parts from message body.
            parts = msg.get_payload()
            # loop for each part
            for n, part in enumerate(parts):
                # print multiple part information by invoke print_info function recursively.
                try:
                    self.print_info(part, indent_number + 1)
                except Exception:
                    log_stack.info('no_indent')
                    return 'no indent'
        # if not multiple part.
        else:
            # get message content mime type
            content_type = msg.get_content_type()
            # if plain text or html content type.
            if content_type == 'text/plain' or content_type == 'text/html':
                # get email content
                content = msg.get_payload(decode=True)
                # get content string charset
                charset = self.guess_charset(msg)
                # decode the content with charset if provided.
                if charset:
                    try:
                        content = content.decode(charset)
                    except Exception:
                        if self.debug:
                            logger.info(
                                f'cant_decode with msg charset {charset}'
                            )
                        try:
                            content = content.decode('cp1251')
                            if self.debug:
                                logger.info('decode with cp1251')
                        except Exception:
                            try:
                                content = content.decode('utf8')
                            except Exception:
                                log_stack.info('cant_decode_content')
                                return ''

            return content

    def get_host(self):
        mailru = {'bk.ru', 'mail.ru', 'inbox.ru', 'list.ru', 'mail.ua'}
        ramblerru = {
            'rambler.ru', 'autorambler.ru', 'lenta.ru', 'myrambler.ru', 'ro.ru'
        }
        gmailcom = {'gmail.com', }

        self.pop_auth = 'user'
        self.pop_port = '995'

        if self.debug:
            logger.info(f'self.mail_host:{self.mail_host}')

        if self.mail_host in mailru:
            self.pop_host = 'pop.mail.ru'
        elif self.mail_host in ramblerru:
            self.pop_host = 'pop.rambler.ru'
        elif self.mail_host in gmailcom:
            self.pop_host = 'pop.gmail.com'
        else:
            self.pop_host = self.mail_host
            self.log('cant_detect_host')

    def create_connection(self):

        try:
            if self.ssl:
                if self.proxy:
                    pop_connection = proxify(
                        POP3_SSL
                    )(
                        self.pop_host,
                        int(self.pop_port),
                        proxy=self.proxy.aio_str
                    )
                else:
                    pop_connection = POP3_SSL(self.pop_host, self.pop_port)
            else:
                if self.proxy:
                    pop_connection = proxify(
                        POP3
                    )(
                        self.pop_host,
                        int(self.pop_port),
                        proxy=self.proxy.aio_str,
                    )
                else:
                    pop_connection = POP3(self.pop_host, self.pop_port)

            return pop_connection
        except Exception:
            log_stack.error(f'catch it 1')
            raise FastReturn

    def connect(self, pop_connection):
        try:
            self.log(
                'POP3.Welcome: ' + pop_connection.getwelcome().decode('utf-8')
            )
        except Exception:
            log_stack.error(f'catch it 2')
            raise FastReturn

    def login(self, pop_connection):
        try:
            pop_connection.user(self.pop_email)
            pop_connection.pass_(self.pop_password)
        except poplib.error_proto as rs:
            rs_str = str(rs)
            # try:
            #     rs_str = rs_str.decode('utf8')
            # except Exception:
            #     pass

            if '-ERR Authentication failed. Please verify your account by going to' in rs_str:
                data = {
                    'need_verify': True, 'resp': rs_str, 'bad': True
                }
                self.log_bad(data=data)
                return MailRet(
                    ok=False, mails=[], log=self.log_return(), data=data
                )
            elif '-ERR Invalid login or password' in rs_str:
                data = {
                    'need_verify': False, 'resp': 'CHECK_LOG_PASS: '+rs_str, 'bad': True, 'pwd': True,
                    'login_password': self.pop_email+'_'+self.pop_password
                }
                self.log_bad(data=data)
                return MailRet(
                    ok=False, mails=[], log=self.log_return(), data=data
                )
            #elif '-ERR internal server error':
            #elif '-ERR [SYS/TEMP] Internal error occurred.'
            else:
                log_stack.error(f'{self.pop_email}:{self.pop_password}')

                data = {
                    'need_verify': False, 'resp': 'CHECK: '+rs_str, 'bad': None
                }
                self.log_bad(data=data)
                return MailRet(
                    ok=False, mails=[], log=self.log_return(), data=data
                )
        except Exception:
            log_stack.error(f'catch it 3')
            raise FastReturn

    def _get_mails(self, pop_connection):
        try:
            resp, mails, octets = pop_connection.list()
            for index in range(len(mails), 1, -1):
                try:
                    resp, lines, octets = pop_connection.retr(index)
                except Exception:
                    continue
                try:
                    msg_content = b'\r\n'.join(lines).decode('utf-8')
                    msg = Parser().parsestr(msg_content)
                    email_cont = self.print_info(msg)
                except UnicodeDecodeError:
                    try:
                        msg_content = b'\r\n'.join(lines).decode('cp1251')
                        msg = Parser().parsestr(msg_content)
                        email_cont = self.print_info(msg)
                    except Exception:
                        log_stack.info(f'cp1251 error')
                        continue
                except Exception as exc:
                    if self.debug:
                        log_stack.error(f'here3')
                    continue

                email_from = msg.get(
                    'From'
                ).lower() if msg.get('From') else msg.get('From')
                email_to = msg.get(
                    'To'
                ).lower() if msg.get('To') else msg.get('To')
                email_subject = msg.get('Subject')
                email_id = msg.get('Message-Id')

                _temp = decode_header(email_subject)
                try:
                    decoded_to = decode_header(email_to)[0][0].decode(_temp[0][1])
                except Exception:
                    decoded_to = email_to

                try:
                    decoded_from = decode_header(email_from)[0][0].decode(_temp[0][1])
                except Exception:
                    decoded_from = email_from

                try:
                    decoded_subj = decode_header(email_subject)[0][0].decode(_temp[0][1])
                except Exception:
                    decoded_subj = email_subject

                self.log(
                    'Message: {} {}. Size: {}'.format(
                        index, pop_connection.stat()[0], pop_connection.stat()[1]
                    )
                )
                if email_id not in self.mails_ids:
                    self.mails_ids.add(email_id)
                    self.mails.append({
                        'id': email_id, 'from': email_from,
                        'to': email_to, 'subject': email_subject,
                        'content': email_cont,
                        'decoded': {
                            'to': decoded_to, 'from': decoded_from,
                            'subj': decoded_subj
                        },
                    })
        except Exception:
            log_stack.error('catch it 3')

    def get_mails(self):

        try:

            pop_connection = self.create_connection()

            self.connect(pop_connection)

            bad_login = self.login(pop_connection)
            if bad_login:
                return bad_login

            self.log('Messages: %s. Size: %s' % pop_connection.stat())

            self._get_mails(pop_connection)

            try:
                pop_connection.quit()
            except Exception:
                pass

            return MailRet(
                ok=True if self.mails else False,
                log=self.log_return(), mails=self.mails
            )

        except FastReturn:
            return MailRet(
                ok=False,
                log=self.log_return()
            )

        except Exception as rs:
            try:
                log_stack.error('get_mails.stack')
                rs_str = str(rs)
                self.log_bad(data={'need_verify': False, 'resp': rs_str})
                tb_str = traceback.format_exception(
                    etype=type(rs), value=rs, tb=rs.__traceback__
                )
                self.log(''.join(tb_str))
            except Exception as exc:
                if self.debug:
                    logger.info(f'here4 {exc}')

            return MailRet(ok=False, mails=[], log=self.log_return())
