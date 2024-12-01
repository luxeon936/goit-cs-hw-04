import os
import time
import threading
from threading import Thread
from multiprocessing import Process, Queue, Manager


def search_keywords_in_file(file_path, keywords):
    """Функція для пошуку ключових слів у файлі."""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        return {keyword: file_path for keyword in keywords if keyword in content}
    except Exception as e:
        print(f"Помилка при обробці файлу {file_path}: {e}")
        return {}


def worker_multiprocessing(files, keywords, output_queue):
    """Worker-функція для multiprocessing."""
    local_results = {}
    for file_path in files:
        result = search_keywords_in_file(file_path, keywords)
        for k, v in result.items():
            if k in local_results:
                local_results[k].append(v)
            else:
                local_results[k] = [v]
    output_queue.put(local_results)


def threaded_search(file_list, keywords):
    """Багатопотоковий пошук ключових слів."""
    import threading

    results = {}
    threads = []
    lock = threading.Lock()

    def worker(files):
        local_results = {}
        for file_path in files:
            result = search_keywords_in_file(file_path, keywords)
            for k, v in result.items():
                if k in local_results:
                    local_results[k].append(v)
                else:
                    local_results[k] = [v]
        with lock:
            for key, value in local_results.items():
                if key in results:
                    results[key].extend(value)
                else:
                    results[key] = value

    # Розділити файли між потоками
    num_threads = 4  # Ви можете змінити кількість потоків
    chunk_size = len(file_list) // num_threads
    for i in range(num_threads):
        start = i * chunk_size
        end = None if i == num_threads - 1 else (i + 1) * chunk_size
        t = Thread(target=worker, args=(file_list[start:end],))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    return results


def multiprocessing_search(file_list, keywords):
    """Багатопроцесорний пошук ключових слів."""
    processes = []
    output_queue = Queue()
    num_processes = 4
    chunk_size = len(file_list) // num_processes

    for i in range(num_processes):
        start = i * chunk_size
        end = None if i == num_processes - 1 else (i + 1) * chunk_size
        p = Process(target=worker_multiprocessing, args=(file_list[start:end], keywords, output_queue))
        processes.append(p)
        p.start()

    for p in processes:
        p.join()

    results = {}
    while not output_queue.empty():
        local_results = output_queue.get()
        for key, value in local_results.items():
            if key in results:
                results[key].extend(value)
            else:
                results[key] = value

    return results


if __name__ == "__main__":
    files = ["text1.txt", "text2.txt", "text3.txt"]
    keywords = ["dummy", "massa", "lectus", "Lorem"]
    files = [f for f in files if os.path.exists(f)]

    start_time = time.time()
    threaded_results = threaded_search(files, keywords)
    print("Threaded Results:", threaded_results)
    print(f"Threaded search completed in {time.time() - start_time:.2f} seconds\n")

    start_time = time.time()
    multiprocessing_results = multiprocessing_search(files, keywords)
    print("Multiprocessing Results:", multiprocessing_results)
    print(f"Multiprocessing search completed in {time.time() - start_time:.2f} seconds")