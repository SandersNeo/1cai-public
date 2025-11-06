# 🚀 PRODUCTION DEPLOYMENT GUIDE - Perfect Setup

**For 10/10 quality deployment**

---

## ✅ PRE-DEPLOYMENT CHECKLIST

### **1. Code Quality** ✅
- [ ] All tests passing (100/100)
- [ ] Coverage > 95%
- [ ] Linting clean (Black, Flake8, MyPy)
- [ ] Security scan clean (Bandit, Snyk)
- [ ] Performance benchmarks met

### **2. Infrastructure** ✅
- [ ] Database migrations ready
- [ ] Backup strategy configured
- [ ] Monitoring setup (Grafana)
- [ ] Logging configured (Loki)
- [ ] Alerts configured (8 rules)

### **3. Security** ✅
- [ ] SSL/TLS certificates installed
- [ ] Environment variables secured
- [ ] API keys rotated
- [ ] Audit logging enabled
- [ ] WAF configured

### **4. Performance** ✅
- [ ] CDN configured
- [ ] Database indexed
- [ ] Caching enabled (Redis)
- [ ] GZip compression on
- [ ] Connection pools tuned

---

## 🎯 DEPLOYMENT STEPS

### **Method 1: Blue-Green Deployment** (Recommended!)

```bash
# 1. Deploy to inactive environment
./deploy/blue-green-deployment.sh v2.1.0

# Script automatically:
# - Deploys to green (if blue is active)
# - Runs health checks
# - Runs smoke tests
# - Verifies performance
# - Switches traffic
# - Monitors for issues
# - Auto-rollback if problems
```

**Advantages:**
- Zero downtime
- Instant rollback
- Safe production updates
- Tested before traffic switch

---

### **Method 2: Rolling Deployment**

```bash
# Update instances one by one
for instance in $(kubectl get pods -l app=api -o name); do
    kubectl set image $instance api=1c-ai-stack:v2.1.0
    kubectl rollout status deployment/api
    sleep 30
done
```

---

### **Method 3: Canary Deployment**

```bash
# Send 10% of traffic to new version
kubectl apply -f deploy/canary-10-percent.yaml

# Monitor metrics for 1 hour
# If good, increase to 50%
kubectl apply -f deploy/canary-50-percent.yaml

# If still good, switch to 100%
kubectl apply -f deploy/canary-100-percent.yaml
```

---

## 📊 POST-DEPLOYMENT VERIFICATION

### **1. Health Check**
```bash
curl -f https://api.1c-ai-stack.com/health
# Must return 200 with "status": "healthy"
```

### **2. Smoke Tests**
```bash
pytest tests/smoke/ --host=https://api.1c-ai-stack.com
# All must pass
```

### **3. Performance Check**
```bash
k6 run tests/load/smoke_perf.js
# p95 must be < 200ms
```

### **4. Monitor Dashboards**
- Grafana: http://grafana.1c-ai-stack.com
- Check: Request rate, error rate, latency
- Watch for: Spikes, errors, slow queries

### **5. Check Logs**
```bash
# Any errors in last 5 minutes?
curl "http://loki.1c-ai-stack.com/api/v1/query?query={level=\"error\"}&limit=100"
```

---

## 🔄 ROLLBACK PROCEDURE

### **If Issues Detected:**

**Blue-Green:**
```bash
# Instant rollback (< 10 seconds)
curl -X POST http://lb.1c-ai-stack.com/switch-active \
  -d '{"active_env": "blue"}'
```

**Kubernetes:**
```bash
# Rollback to previous version
kubectl rollout undo deployment/api
kubectl rollout status deployment/api
```

**Docker Compose:**
```bash
# Switch to previous tag
docker-compose down
docker-compose -f docker-compose.previous.yml up -d
```

---

## 📈 MONITORING POST-DEPLOY

### **Key Metrics to Watch (First 24 hours):**

1. **Error Rate** (Target: < 0.1%)
   - Monitor: `rate(http_requests_total{status=~"5.."}[5m])`
   - Alert if: > 1%

2. **Response Time** (Target: p95 < 200ms)
   - Monitor: `histogram_quantile(0.95, http_request_duration_seconds)`
   - Alert if: > 500ms

3. **Throughput** (Baseline: Current load)
   - Monitor: `rate(http_requests_total[5m])`
   - Alert if: Drops >  20%

4. **Database** (Target: < 80% pool usage)
   - Monitor: `database_pool_active / database_pool_max`
   - Alert if: > 90%

5. **Memory** (Target: < 80%)
   - Monitor: `node_memory_usage_percent`
   - Alert if: > 90%

---

## ✅ DEPLOYMENT SUCCESS CRITERIA

### **All Must Be Green:**
- [x] Health check: 200 OK
- [x] All smoke tests pass
- [x] Error rate < 0.1%
- [x] p95 latency < 200ms
- [x] No alerts firing
- [x] Logs clean (no errors)
- [x] Database responsive
- [x] All 6 dashboards load

**IF ALL GREEN → DEPLOYMENT SUCCESS!** ✅

---

## 🎯 PRODUCTION BEST PRACTICES

1. **Always deploy during low-traffic hours**
2. **Have DBA on standby for database issues**
3. **Monitor for at least 1 hour post-deploy**
4. **Keep rollback ready for 24 hours**
5. **Document any issues in post-mortem**
6. **Update runbooks based on learnings**

---

**PERFECT DEPLOYMENT PROCESS!** 🚀✨


