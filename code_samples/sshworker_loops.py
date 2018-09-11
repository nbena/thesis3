class SSHBackgroundWorker(object):

    def __init__(self):

        self.__main_queue = queue.Queue()
        self.__main_conn = conns.ConnManager()
        self.__main_worker_thread = threading.Thread(
            target=self.__main_loop_func)

        self.__crl_queue = queue.Queue()
        self.__crl_conn = conns.ConnManager()
        self.__crl_worker_thread = threading.Thread(
            target=self.__crl_loop_func)

        self.__thread_number = 2

        self.__redis_conn = redis_conn.RedisConn(
            threads_number=self.__thread_number)

    def __main_loop_func(self):
        loop = True
        while loop is True:
            work = self.__main_queue.get()
            if work is not None:

                work_type = work['work_type']
                work_id = work['work_id']
                self.__work_pre(work_id)
                result = None

                if work_type == status.WorkType.transfer_client.value:
                    result = self.__transfer_client(work)
                elif work_type == status.WorkType.transfer_server.value:
                    result = self.__transfer_server(work)
                elif (work_type == status.WorkType.renew_server.value):
                    result = self.__renew_server_cert(work)
                elif work_type == status.WorkType.revoke_client.value:
                    result = self.__deleteclient(work)

                if result is not None:
                    self.__work_post(work_id, result)

            else:
                loop = False

    def __crl_loop_func(self):
        loop = True
        while loop is True:
            work = self.__crl_queue.get()
            if work is not None:

                work_type = work['work_type']
                work_id = work['work_id']

                self.__work_pre(work_id)

                if status.is_crl_str(work_type):
                    result = self.__update_crl(work)
                    self.__work_post(work_id, result)
            else:
                loop = False

    def __work_post(self, work_id, result):

        if result['is_error']:
            if isinstance(result, tuple):
                error_str = str(result[1])
            else:
                error_str = result
            self.__redis_conn.set_work_status(
                work_id, status.WorkStatus.error,
                error_str)

    def __work_pre(self, work_id):

        self.__redis_conn.set_work_status(work_id, status.WorkStatus.working)
