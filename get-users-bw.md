DASH Users Bandwidth
========================================================

For using this script, first it is needed to download the dash dataset at [http://media.polito.it/mmsys14-dataset/neubot-dash-dataset-mmsys14.readme.md](http://media.polito.it/mmsys14-dataset/neubot-dash-dataset-mmsys14.readme.md).
After use the python script convert-json-to-csv.py to convert the dataset to csv.
This script will use the csv file as an input and will produce a .dat file with users and their bandwidth distribution for each of the chosen dash rates.

The result will be a [user x rate] matrix. Each element in the matrix is a "userU_rateR" value that represents the fraction of the time (i.e. a value between 0 and 1) which user "U" has a bandwidth throughput smaller than rate "R". An example with 2 users and 4 rates will be:


|        | 1000kbps | 2000kbps | 3000kbps | 4000kbps |
|:------:|---------:|---------:|---------:|---------:|
| user 1 |        0	|      0.4 |      0.7 |      0.9 |
| user 2 |      0.2	|      0.6 |        1 |        1 |

  
The result file is a plain text .dat [user x rate] matrix, using the first example the final file it will be something like:
[[0, 0.4, 0.7, 0.9],[0.2, 0.6, 1, 1]]

The selection of rates range is:  from 150 kbps up to 12600 kbps with a step of 50 kbps. In total 250 points.

For the users we will select a subset depend on the filtering criterion:
  * average criterion
  * 75th percentile criterion
  
Which means two different output files, accordingly to the users subset, will be produce.


```r
# Settings
rates_kbps = seq(150, 12600, by = 50)  # dash bitrates 
max_users = 1000  # maximum number of users returned
# script will take the max_users that have most samples and meet the
# criteria
min_samples = 100  # minimum ammount of samples a user should have, less than that user will be discarted
criteria_bw_kbps = 8000  # limit of the criterias

bps_to_kbps = 1024
bps_to_mbps = 1048576

path = "/Users/karine/phd/data/dash-users/neubot-parsed/"

# Libraries
library("plyr")
library("foreach")
library("ggplot2")
options(scipen = 100)
parallel = TRUE
```




```r

# List of users with problems, i.e. impossible bw capacity
black_list_users = c("0d929236-fc4e-4319-ab49-e08fbcc4a744")


f = paste(path, "201311-201401.csv", sep = "")
if (file.exists(f)) {
    da = read.csv(f)
} else {
    # Load the csv input files
    files = c("201311.csv", "201312.csv", "201401.csv")
    d = data.frame()
    for (file in files) {
        ft = paste(path, file, sep = "")
        t = read.csv(ft)
        d = rbind(d, t)
    }
    
    # Remove initial points (adaptation of dash)
    da = d[d$client_iteration > 4, ]
    write.csv(da, f, quote = FALSE, row.names = FALSE)
    d = NULL
}

# Calculate the bandwidth throughput based on bytes received and time
# elapsed
da$bw = da$client_received/da$client_elapsed  # bytes per second
da$bw_bits = da$bw * 8  # bits per second
da$bw_mpbs = da$bw_bits/bps_to_mbps

# Create new user id based on ip + uuid
da$ipuserid = paste(da$client_real_address, "-", da$client_uuid, sep = "")

f = paste(path, "user-statistics.csv", sep = "")
if (file.exists(f)) {
    du = read.csv(f)
} else {
    # Calculate the number of samples, average and 75% of all users
    (z <- Sys.time())
    du = ddply(da, ~ipuserid, summarize, .parallel = parallel, samples = length(ipuserid), 
        min = min(bw_bits), mean = mean(bw_bits), median = median(bw_bits), 
        max = max(bw_bits), stdv = sd(bw_bits), percentile75 = quantile(bw_bits, 
            0.75))
    (z <- Sys.time())
    write.csv(du, f, quote = FALSE, row.names = FALSE)
}
```


Verification of some users:


```r

user_index = 1
d1u = da[da$ipuserid == as.character(du$ipuserid[user_index]), ]
plot(qplot(d1u$bw_mpbs, stat = "ecdf", geom = "step", xlab = "bandwidth (Mbps)", 
    ylab = "samples"))
```

![plot of chunk user_example](figure/user_example.png) 


Select the subset accordingly to the criterias:


```r
f_avg = paste(path, "dash_users_avg.dat", sep = "")
f_perc = paste(path, "dash_users_75perc.dat", sep = "")
if (file.exists(f_avg) && file.exists(f_perc)) {
    print("Output files already exists. Delete manually to recreate.")
} else {
    criteria_bw_bps = criteria_bw_kbps * bps_to_kbps
    
    # Users that meet average criteria and samples
    du_avg = du[du$mean < criteria_bw_bps & du$samples >= min_samples, ]  # & !(du$client_uuid %in% black_list_users) not needed since the bw criteria will cut this users
    du_avg = du_avg[order(-du_avg$samples), ]  # order by the number of samples
    # If we have more than needed we take only max_users with more samples
    if (length(du_avg$ipuserid) > max_users) {
        du_avg = du_avg[1:max_users, ]
    }
    
    
    # Users that meet percentile criteria and samples
    du_perc = du[du$percentile75 < criteria_bw_bps & du$samples >= min_samples, 
        ]
    du_perc = du_perc[order(-du_perc$samples), ]  # order by the number of samples
    # If we have more than needed we take only max_users with more samples
    if (length(du_perc$ipuserid) > max_users) {
        du_perc = du_perc[1:max_users, ]
    }
}
```

```
## [1] "Output files already exists. Delete manually to recreate."
```


Create the matrix [user x rates]:


```r

if (!(file.exists(f_avg) && file.exists(f_perc))) {
    rates_bps = rates_kbps * bps_to_kbps
    
    mu_avg = matrix(nrow = length(du_avg$ipuserid), ncol = length(rates_bps))
    for (user_index in 1:length(du_avg$ipuserid)) {
        t = da[da$ipuserid == as.character(du_avg$ipuserid[user_index]), ]
        fnecdf = ecdf(t$bw_bits)
        mu_avg[user_index, ] = fnecdf(rates_bps)
    }
    
    mu_perc = matrix(nrow = length(du_perc$ipuserid), ncol = length(rates_bps))
    for (user_index in 1:length(du_perc$ipuserid)) {
        t = da[da$ipuserid == as.character(du_perc$ipuserid[user_index]), ]
        fnecdf = ecdf(t$bw_bits)
        mu_perc[user_index, ] = fnecdf(rates_bps)
    }
}
```


Output the results:


```r
if (!(file.exists(f_avg) && file.exists(f_perc))) {
    matrix2dat <- function(m) {
        mfinal = apply(m, 1, paste, sep = "", collapse = ",")
        mfinal = paste("[", mfinal, "]", sep = "", collapse = ",")
        mfinal = paste("[", mfinal, "]", sep = "")
        return(paste(mfinal, sep = "", collapse = ","))
    }
    
    write(matrix2dat(mu_avg), file = f_avg)
    write(matrix2dat(mu_perc), file = f_perc)
}
```



