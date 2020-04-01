## Restart Frank
```
systemctl restart frank
```

## Frank Directory
```
/root/cc-frank
```

## Frank Deployment
```
Primary Frank (WA1): 10.88.10.202
Secondary Frank (UC1): 10.124.15.156
```

## Frank Logs
```
/root/cc-frank/frank.log
```

## Troubleshooting Frank
- SSH to WA1 Noc Box
To restart Frank:
```
ssh root@10.88.10.202
systemctl status frank 
systemctl restart frank
systemctl status frank
```

If Primary Frank is unresponsive, login to Secondary Frank (10.124.15.156)
```
ssh root@10.124.15.156
systemctl start frank
```
