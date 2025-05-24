import sys,os,asyncio,argparse,importlib,re,multiprocessing,traceback,uuid
from croniter import croniter
import datetime,time

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.super.ESModel import connetES
from src.entity.ETask import ETask



async def start_consumer(consumer_id):
    print('consumer started:',consumer_id)
    async for task in ETask.fetch(consumer_id=consumer_id):
        if not task:
            await asyncio.sleep(2)
            continue
        print('consumer:',task._id,task.title)
        try:
            if task.cron_enabled:
                now                     = datetime.datetime.now()
                cron                    = croniter(task.cron_expr, now)
                prev_time               = cron.get_prev(datetime.datetime)
                prev_time_minute        = prev_time.replace(second=0, microsecond=0)
                now_minute              = now.replace(second=0, microsecond=0)
                if prev_time_minute == now_minute:
                    await task.consumer(consumer_id=consumer_id)
                next_time               = cron.get_next(datetime.datetime)
                next_time               = next_time.strftime("%Y-%m-%d %H:%M:%S")
                await task.upset(status='pending',status_description='', success=task.success+1,schedule_time=next_time,refresh=True)
            else:
                await task.consumer(consumer_id=consumer_id)
                await task.upset(status='completed',status_description='', success=task.success+1)
        except Exception as e:
            print('consumer error:',traceback.format_exc())
            await task.upset(status='failed',status_description=str(e),failure=task.failure+1)

def start_process(consumer_id):
    asyncio.run(start_consumer(consumer_id))

def create_process():
    consumer_id                         = f"worker-{uuid.uuid4()}" 
    process                             = multiprocessing.Process(target=start_process, args=(consumer_id,))
    process.start()
    return consumer_id,process
    
if __name__ == '__main__':
    process_list                             = {}
    parser                              = argparse.ArgumentParser()
    parser.add_argument('-n','--process', type=int, required=False, default=5, help='消费者线程数量 (default: 5)')
    args                                = parser.parse_args()
    for i in range(args.process):
        consumer_id,process             = create_process() 
        process_list[consumer_id]       = process

    while True:
        for consumer_id,process in process_list.items():
            if not process.is_alive():
                print(f'线程 {consumer_id} 已终止，正在重启...')
                consumer_id,process      = create_process() 
                process_list[consumer_id]= process
        time.sleep(1)
    