import psycopg2
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()

DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'hospital_db')
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'postgres')

def get_db_connection():
    """Database bağlantısı"""
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )

def calculate_percentile(latencies, percentile):
    """Percentile hesapla"""
    if not latencies:
        return 0
    sorted_latencies = sorted(latencies)
    index = int(len(sorted_latencies) * percentile / 100)
    return sorted_latencies[min(index, len(sorted_latencies) - 1)]

def get_performance_metrics(architecture='SOA', hours=24):
    """Performance metriklerini hesapla"""
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    since = datetime.now() - timedelta(hours=hours)
    
    cursor.execute("""
        SELECT latency_ms, status, timestamp
        FROM event_log
        WHERE architecture = %s
        AND timestamp > %s
        AND latency_ms IS NOT NULL
        ORDER BY latency_ms
    """, (architecture, since))
    
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    
    if not results:
        return {
            'architecture': architecture,
            'period_hours': hours,
            'total_requests': 0,
            'error': 'No data available'
        }
    
    latencies = [r[0] for r in results if r[1] == 'SUCCESS']
    total_requests = len(results)
    successful_requests = len(latencies)
    failed_requests = total_requests - successful_requests
    
    if not latencies:
        return {
            'architecture': architecture,
            'period_hours': hours,
            'total_requests': total_requests,
            'successful_requests': 0,
            'failed_requests': failed_requests,
            'success_rate': 0.0,
            'error': 'No successful requests'
        }
    
    metrics = {
        'architecture': architecture,
        'period_hours': hours,
        'total_requests': total_requests,
        'successful_requests': successful_requests,
        'failed_requests': failed_requests,
        'success_rate': round((successful_requests / total_requests) * 100, 2),
        'latency': {
            'min': min(latencies),
            'max': max(latencies),
            'avg': round(sum(latencies) / len(latencies), 2),
            'p50': calculate_percentile(latencies, 50),
            'p95': calculate_percentile(latencies, 95),
            'p99': calculate_percentile(latencies, 99)
        },
        'throughput': {
            'requests_per_hour': round(total_requests / hours, 2),
            'requests_per_minute': round(total_requests / (hours * 60), 2)
        }
    }
    
    return metrics

def print_performance_report():
    """Performance raporunu yazdır"""
    
    print("\n" + "="*70)
    print("📊 PERFORMANCE METRICS REPORT")
    print("="*70)
    
    soa_metrics = get_performance_metrics('SOA', hours=24)
    
    print("\n🔷 SOA (SOAP) Architecture")
    print("-"*70)
    if 'error' not in soa_metrics:
        print(f"Total Requests: {soa_metrics['total_requests']}")
        print(f"Success Rate: {soa_metrics['success_rate']}%")
        print(f"\nLatency:")
        print(f"  Min: {soa_metrics['latency']['min']}ms")
        print(f"  Avg: {soa_metrics['latency']['avg']}ms")
        print(f"  P50: {soa_metrics['latency']['p50']}ms")
        print(f"  P95: {soa_metrics['latency']['p95']}ms")
        print(f"  P99: {soa_metrics['latency']['p99']}ms")
        print(f"  Max: {soa_metrics['latency']['max']}ms")
        print(f"\nThroughput:")
        print(f"  {soa_metrics['throughput']['requests_per_hour']} req/hour")
        print(f"  {soa_metrics['throughput']['requests_per_minute']} req/min")
    else:
        print(f"⚠️  {soa_metrics['error']}")
    
    serverless_metrics = get_performance_metrics('SERVERLESS', hours=24)
    
    print("\n🔶 Serverless Architecture")
    print("-"*70)
    if 'error' not in serverless_metrics:
        print(f"Total Events: {serverless_metrics['total_requests']}")
        print(f"Success Rate: {serverless_metrics['success_rate']}%")
        print(f"\nLatency:")
        print(f"  Min: {serverless_metrics['latency']['min']}ms")
        print(f"  Avg: {serverless_metrics['latency']['avg']}ms")
        print(f"  P50: {serverless_metrics['latency']['p50']}ms")
        print(f"  P95: {serverless_metrics['latency']['p95']}ms")
        print(f"  P99: {serverless_metrics['latency']['p99']}ms")
        print(f"  Max: {serverless_metrics['latency']['max']}ms")
        print(f"\nThroughput:")
        print(f"  {serverless_metrics['throughput']['requests_per_hour']} events/hour")
        print(f"  {serverless_metrics['throughput']['requests_per_minute']} events/min")
    else:
        print(f"⚠️  {serverless_metrics['error']}")
    
    if 'error' not in soa_metrics and 'error' not in serverless_metrics:
        print("\n📈 Comparison (SOA vs Serverless)")
        print("-"*70)
        soa_p95 = soa_metrics['latency']['p95']
        serverless_p95 = serverless_metrics['latency']['p95']
        improvement = round(((soa_p95 - serverless_p95) / soa_p95) * 100, 2) if soa_p95 > 0 else 0
        
        print(f"P95 Latency:")
        print(f"  SOA: {soa_p95}ms")
        print(f"  Serverless: {serverless_p95}ms")
        if improvement > 0:
            print(f"  Improvement: {improvement}% faster")
        else:
            print(f"  Difference: {abs(improvement)}%")
    
    print("\n" + "="*70)

if __name__ == "__main__":
    print_performance_report()