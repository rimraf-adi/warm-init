# Results

Generated from `results/runs.jsonl`; do not edit by hand.
Runs logged: 124

## Stage: phase0-smoke

| run | target | donor | init | budget h | seed | WER | CER | tone CER | tone chars | CI | utts | status | commit |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| phase0-smoke-dogri-own-head-1791830106 | dogri | hi | own-head |  |  |  | 0.406 | 0.822 | 326 |  | 40 | done | 6fdbff6* |
| phase0-smoke-dogri-own-head-1791830117 | dogri | hi | own-head |  |  |  | 0.420 | 0.807 | 326 |  | 40 | done | 6fdbff6* |
| phase0-smoke-dogri-own-head-doi-1791830540 | dogri | hi | own-head-doi |  |  |  | 1.000 | 1.000 | 1282 |  | 200 | done | c220276* |
| phase0-smoke-dogri-own-head-doi-1791831436 | dogri | hi | own-head-doi |  |  |  | 41.463 | 0.132 | 1282 |  | 200 | done | c220276* |
| phase0-smoke-dogri-own-head-doi-INVALID-1791831460 | dogri | hi | own-head-doi-INVALID |  |  |  |  |  |  |  | 200 | invalid | c220276* |
| phase0-smoke-dogri-own-head-doi-INVALID-1791831460 | dogri | hi | own-head-doi-INVALID |  |  |  |  |  |  |  | 200 | invalid | c220276* |
| phase0-smoke-dogri-zero-shot-hi-1791830235 | dogri | hi | zero-shot-hi |  |  |  | 0.413 | 0.794 | 1282 |  | 200 | done | 9bb9189* |
| phase0-smoke-dogri-zero-shot-hi-1791830287 | dogri | hi | zero-shot-hi |  |  |  | 0.422 | 0.789 | 1282 |  | 200 | done | 9bb9189* |

## Stage: phase1

| run | target | donor | init | budget h | seed | WER | CER | tone CER | tone chars | CI | utts | status | commit |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| phase1-dogri-donor-bn-1791843299 | dogri | bn | donor-bn | 0.262 | 0 | 0.446 | 0.202 | 0.240 | 4852 |  | 969 | done | 0b23bd0* |
| phase1-dogri-donor-bn-1791843661 | dogri | bn | donor-bn | 0.262 | 1 | 0.444 | 0.202 | 0.241 | 4852 |  | 969 | done | 0b23bd0* |
| phase1-dogri-donor-bn-1791844036 | dogri | bn | donor-bn | 0.262 | 2 | 0.445 | 0.202 | 0.246 | 4852 |  | 969 | done | 0b23bd0* |
| phase1-dogri-donor-bn-1791844416 | dogri | bn | donor-bn | 1.020 | 0 | 0.368 | 0.168 | 0.151 | 4852 |  | 969 | done | 0b23bd0* |
| phase1-dogri-donor-bn-1791844806 | dogri | bn | donor-bn | 1.020 | 1 | 0.369 | 0.168 | 0.150 | 4852 |  | 969 | done | 0b23bd0* |
| phase1-dogri-donor-bn-1791845201 | dogri | bn | donor-bn | 1.020 | 2 | 0.368 | 0.168 | 0.152 | 4852 |  | 969 | done | 0b23bd0* |
| phase1-dogri-donor-hi-1791842942 | dogri | hi | donor-hi | 0.262 | 0 | 0.431 | 0.193 | 0.241 | 4852 |  | 969 | done | 0b23bd0* |
| phase1-dogri-donor-hi+comp-1791845618 | dogri | hi | donor-hi+comp | 0.262 | 0 | 0.423 | 0.189 | 0.232 | 4852 |  | 969 | done | e47bd39* |
| phase1-dogri-donor-hi+comp-1791845976 | dogri | hi | donor-hi+comp | 0.262 | 1 | 0.422 | 0.189 | 0.233 | 4852 |  | 969 | done | e47bd39* |
| phase1-dogri-donor-hi+comp-1791846336 | dogri | hi | donor-hi+comp | 0.262 | 2 | 0.423 | 0.190 | 0.232 | 4852 |  | 969 | done | e47bd39* |
| phase1-dogri-donor-hi+comp-1791846705 | dogri | hi | donor-hi+comp | 1.020 | 0 | 0.369 | 0.166 | 0.152 | 4852 |  | 969 | done | e47bd39* |
| phase1-dogri-donor-hi+comp-1791847086 | dogri | hi | donor-hi+comp | 1.020 | 1 | 0.366 | 0.165 | 0.147 | 4852 |  | 969 | done | e47bd39* |
| phase1-dogri-donor-hi+comp-1791847466 | dogri | hi | donor-hi+comp | 1.020 | 2 | 0.366 | 0.165 | 0.146 | 4852 |  | 969 | done | e47bd39* |
| phase1-dogri-donor-hi+comp+noblank-1791847961 | dogri | hi | donor-hi+comp+noblank | 0.262 | 0 | 0.451 | 0.201 | 0.197 | 4852 |  | 969 | done | d76e001* |
| phase1-dogri-donor-hi+comp+noblank-1791848339 | dogri | hi | donor-hi+comp+noblank | 0.262 | 1 | 0.451 | 0.201 | 0.202 | 4852 |  | 969 | done | d76e001* |
| phase1-dogri-donor-hi+comp+noblank-1791848715 | dogri | hi | donor-hi+comp+noblank | 0.262 | 2 | 0.449 | 0.200 | 0.195 | 4852 |  | 969 | done | d76e001* |
| phase1-dogri-donor-hi+mean-1791845527 | dogri | hi | donor-hi+mean | 0.262 | 0 | 0.436 | 0.196 | 0.256 | 4852 |  | 969 | done | e47bd39* |
| phase1-dogri-donor-hi+mean-1791845886 | dogri | hi | donor-hi+mean | 0.262 | 1 | 0.435 | 0.195 | 0.256 | 4852 |  | 969 | done | e47bd39* |
| phase1-dogri-donor-hi+mean-1791846245 | dogri | hi | donor-hi+mean | 0.262 | 2 | 0.436 | 0.196 | 0.256 | 4852 |  | 969 | done | e47bd39* |
| phase1-dogri-donor-hi+mean-1791846609 | dogri | hi | donor-hi+mean | 1.020 | 0 | 0.369 | 0.167 | 0.160 | 4852 |  | 969 | done | e47bd39* |
| phase1-dogri-donor-hi+mean-1791846990 | dogri | hi | donor-hi+mean | 1.020 | 1 | 0.369 | 0.166 | 0.158 | 4852 |  | 969 | done | e47bd39* |
| phase1-dogri-donor-hi+mean-1791847370 | dogri | hi | donor-hi+mean | 1.020 | 2 | 0.369 | 0.166 | 0.157 | 4852 |  | 969 | done | e47bd39* |
| phase1-dogri-donor-hi+noblank-1791847862 | dogri | hi | donor-hi+noblank | 0.262 | 0 | 0.449 | 0.200 | 0.210 | 4852 |  | 969 | done | d76e001* |
| phase1-dogri-donor-hi+noblank-1791848244 | dogri | hi | donor-hi+noblank | 0.262 | 1 | 0.446 | 0.198 | 0.208 | 4852 |  | 969 | done | d76e001* |
| phase1-dogri-donor-hi+noblank-1791848620 | dogri | hi | donor-hi+noblank | 0.262 | 2 | 0.444 | 0.197 | 0.206 | 4852 |  | 969 | done | d76e001* |
| phase1-dogri-donor-mr-1791843121 | dogri | mr | donor-mr | 0.262 | 0 | 0.438 | 0.196 | 0.246 | 4852 |  | 969 | done | 0b23bd0* |
| phase1-dogri-donor-mr-1791843478 | dogri | mr | donor-mr | 0.262 | 1 | 0.437 | 0.197 | 0.251 | 4852 |  | 969 | done | 0b23bd0* |
| phase1-dogri-donor-mr-1791843850 | dogri | mr | donor-mr | 0.262 | 2 | 0.438 | 0.197 | 0.251 | 4852 |  | 969 | done | 0b23bd0* |
| phase1-dogri-donor-mr-1791844226 | dogri | mr | donor-mr | 1.020 | 0 | 0.373 | 0.168 | 0.154 | 4852 |  | 969 | done | 0b23bd0* |
| phase1-dogri-donor-mr-1791844615 | dogri | mr | donor-mr | 1.020 | 1 | 0.371 | 0.167 | 0.154 | 4852 |  | 969 | done | 0b23bd0* |
| phase1-dogri-donor-mr-1791845011 | dogri | mr | donor-mr | 1.020 | 2 | 0.370 | 0.166 | 0.148 | 4852 |  | 969 | done | 0b23bd0* |
| phase1-dogri-donor-ne-1791843210 | dogri | ne | donor-ne | 0.262 | 0 | 0.438 | 0.196 | 0.231 | 4852 |  | 969 | done | 0b23bd0* |
| phase1-dogri-donor-ne-1791843572 | dogri | ne | donor-ne | 0.262 | 1 | 0.439 | 0.197 | 0.230 | 4852 |  | 969 | done | 0b23bd0* |
| phase1-dogri-donor-ne-1791843942 | dogri | ne | donor-ne | 0.262 | 2 | 0.440 | 0.197 | 0.230 | 4852 |  | 969 | done | 0b23bd0* |
| phase1-dogri-donor-ne-1791844321 | dogri | ne | donor-ne | 1.020 | 0 | 0.370 | 0.166 | 0.146 | 4852 |  | 969 | done | 0b23bd0* |
| phase1-dogri-donor-ne-1791844710 | dogri | ne | donor-ne | 1.020 | 1 | 0.369 | 0.166 | 0.144 | 4852 |  | 969 | done | 0b23bd0* |
| phase1-dogri-donor-ne-1791845106 | dogri | ne | donor-ne | 1.020 | 2 | 0.366 | 0.165 | 0.140 | 4852 |  | 969 | done | 0b23bd0* |
| phase1-dogri-donor-pa-1791843031 | dogri | pa | donor-pa | 0.262 | 0 | 0.454 | 0.205 | 0.243 | 4852 |  | 969 | done | 0b23bd0* |
| phase1-dogri-donor-pa-1791843388 | dogri | pa | donor-pa | 0.262 | 1 | 0.454 | 0.205 | 0.245 | 4852 |  | 969 | done | 0b23bd0* |
| phase1-dogri-donor-pa-1791843751 | dogri | pa | donor-pa | 0.262 | 2 | 0.454 | 0.204 | 0.245 | 4852 |  | 969 | done | 0b23bd0* |
| phase1-dogri-donor-pa-1791844131 | dogri | pa | donor-pa | 1.020 | 0 | 0.374 | 0.169 | 0.153 | 4852 |  | 969 | done | 0b23bd0* |
| phase1-dogri-donor-pa-1791844518 | dogri | pa | donor-pa | 1.020 | 1 | 0.372 | 0.169 | 0.152 | 4852 |  | 969 | done | 0b23bd0* |
| phase1-dogri-donor-pa-1791844911 | dogri | pa | donor-pa | 1.020 | 2 | 0.373 | 0.169 | 0.151 | 4852 |  | 969 | done | 0b23bd0* |
| phase1-dogri-donor-pa+comp-1791845797 | dogri | pa | donor-pa+comp | 0.262 | 0 | 0.461 | 0.206 | 0.238 | 4852 |  | 969 | done | e47bd39* |
| phase1-dogri-donor-pa+comp-1791846156 | dogri | pa | donor-pa+comp | 0.262 | 1 | 0.460 | 0.206 | 0.238 | 4852 |  | 969 | done | e47bd39* |
| phase1-dogri-donor-pa+comp-1791846515 | dogri | pa | donor-pa+comp | 0.262 | 2 | 0.461 | 0.206 | 0.238 | 4852 |  | 969 | done | e47bd39* |
| phase1-dogri-donor-pa+comp-1791846896 | dogri | pa | donor-pa+comp | 1.020 | 0 | 0.377 | 0.170 | 0.156 | 4852 |  | 969 | done | e47bd39* |
| phase1-dogri-donor-pa+comp-1791847276 | dogri | pa | donor-pa+comp | 1.020 | 1 | 0.376 | 0.170 | 0.156 | 4852 |  | 969 | done | e47bd39* |
| phase1-dogri-donor-pa+comp-1791847655 | dogri | pa | donor-pa+comp | 1.020 | 2 | 0.375 | 0.170 | 0.155 | 4852 |  | 969 | done | e47bd39* |
| phase1-dogri-donor-pa+comp+noblank-1791848151 | dogri | pa | donor-pa+comp+noblank | 0.262 | 0 | 0.489 | 0.216 | 0.219 | 4852 |  | 969 | done | d76e001* |
| phase1-dogri-donor-pa+comp+noblank-1791848527 | dogri | pa | donor-pa+comp+noblank | 0.262 | 1 | 0.491 | 0.216 | 0.218 | 4852 |  | 969 | done | d76e001* |
| phase1-dogri-donor-pa+comp+noblank-1791848902 | dogri | pa | donor-pa+comp+noblank | 0.262 | 2 | 0.485 | 0.214 | 0.217 | 4852 |  | 969 | done | d76e001* |
| phase1-dogri-donor-pa+mean-1791845707 | dogri | pa | donor-pa+mean | 0.262 | 0 | 0.462 | 0.208 | 0.257 | 4852 |  | 969 | done | e47bd39* |
| phase1-dogri-donor-pa+mean-1791846066 | dogri | pa | donor-pa+mean | 0.262 | 1 | 0.463 | 0.209 | 0.258 | 4852 |  | 969 | done | e47bd39* |
| phase1-dogri-donor-pa+mean-1791846425 | dogri | pa | donor-pa+mean | 0.262 | 2 | 0.462 | 0.208 | 0.260 | 4852 |  | 969 | done | e47bd39* |
| phase1-dogri-donor-pa+mean-1791846800 | dogri | pa | donor-pa+mean | 1.020 | 0 | 0.376 | 0.170 | 0.161 | 4852 |  | 969 | done | e47bd39* |
| phase1-dogri-donor-pa+mean-1791847180 | dogri | pa | donor-pa+mean | 1.020 | 1 | 0.374 | 0.170 | 0.160 | 4852 |  | 969 | done | e47bd39* |
| phase1-dogri-donor-pa+mean-1791847560 | dogri | pa | donor-pa+mean | 1.020 | 2 | 0.376 | 0.170 | 0.159 | 4852 |  | 969 | done | e47bd39* |
| phase1-dogri-donor-pa+noblank-1791848057 | dogri | pa | donor-pa+noblank | 0.262 | 0 | 0.485 | 0.214 | 0.218 | 4852 |  | 969 | done | d76e001* |
| phase1-dogri-donor-pa+noblank-1791848433 | dogri | pa | donor-pa+noblank | 0.262 | 1 | 0.483 | 0.213 | 0.215 | 4852 |  | 969 | done | d76e001* |
| phase1-dogri-donor-pa+noblank-1791848808 | dogri | pa | donor-pa+noblank | 0.262 | 2 | 0.484 | 0.213 | 0.216 | 4852 |  | 969 | done | d76e001* |
| phase1-dogri-hindi-1791832790 | dogri | hi | hindi | 0.262 | 0 | 0.669 | 0.331 | 0.501 | 4852 |  | 969 | done | a57c406* |
| phase1-dogri-hindi-1791833880 | dogri | hi | hindi | 0.262 | 0 | 0.669 | 0.331 | 0.501 | 4852 |  | 969 | done | 7f5ba89* |
| phase1-dogri-hindi-1791840821 | dogri | hi | hindi | 0.262 | 0 | 0.431 | 0.193 | 0.241 | 4852 |  | 969 | done | 1f7a844* |
| phase1-dogri-hindi-1791834921 | dogri | hi | hindi | 0.262 | 1 | 0.669 | 0.334 | 0.496 | 4852 |  | 969 | done | 7f5ba89* |
| phase1-dogri-hindi-1791841003 | dogri | hi | hindi | 0.262 | 1 | 0.430 | 0.193 | 0.242 | 4852 |  | 969 | done | 1f7a844* |
| phase1-dogri-hindi-1791835979 | dogri | hi | hindi | 0.262 | 2 | 0.668 | 0.333 | 0.501 | 4852 |  | 969 | done | 7f5ba89* |
| phase1-dogri-hindi-1791841185 | dogri | hi | hindi | 0.262 | 2 | 0.432 | 0.193 | 0.245 | 4852 |  | 969 | done | 1f7a844* |
| phase1-dogri-hindi-1791837190 | dogri | hi | hindi | 1.020 | 0 | 0.603 | 0.294 | 0.403 | 4852 |  | 969 | done | 7f5ba89* |
| phase1-dogri-hindi-1791841376 | dogri | hi | hindi | 1.020 | 0 | 0.367 | 0.165 | 0.152 | 4852 |  | 969 | done | 1f7a844* |
| phase1-dogri-hindi-1791838763 | dogri | hi | hindi | 1.020 | 1 | 0.607 | 0.296 | 0.405 | 4852 |  | 969 | done | a08bc1b* |
| phase1-dogri-hindi-1791841573 | dogri | hi | hindi | 1.020 | 1 | 0.368 | 0.166 | 0.154 | 4852 |  | 969 | done | 1f7a844* |
| phase1-dogri-hindi-1791839556 | dogri | hi | hindi | 1.020 | 2 | 0.605 | 0.295 | 0.415 | 4852 |  | 969 | done | 28e6dc8* |
| phase1-dogri-hindi-1791841769 | dogri | hi | hindi | 1.020 | 2 | 0.369 | 0.166 | 0.158 | 4852 |  | 969 | done | 1f7a844* |
| phase1-dogri-hindi-1791839782 | dogri | hi | hindi | 5.016 | 0 | 0.550 | 0.261 | 0.326 | 4852 |  | 969 | done | 28e6dc8* |
| phase1-dogri-hindi-1791842031 | dogri | hi | hindi | 5.016 | 0 | 0.342 | 0.158 | 0.139 | 4852 |  | 969 | done | 1f7a844* |
| phase1-dogri-hindi-1791840011 | dogri | hi | hindi | 5.016 | 1 | 0.555 | 0.263 | 0.351 | 4852 |  | 969 | done | 28e6dc8* |
| phase1-dogri-hindi-1791842272 | dogri | hi | hindi | 5.016 | 1 | 0.341 | 0.157 | 0.133 | 4852 |  | 969 | done | 1f7a844* |
| phase1-dogri-hindi-1791840238 | dogri | hi | hindi | 5.016 | 2 | 0.555 | 0.264 | 0.339 | 4852 |  | 969 | done | 28e6dc8* |
| phase1-dogri-hindi-1791842508 | dogri | hi | hindi | 5.016 | 2 | 0.342 | 0.157 | 0.140 | 4852 |  | 969 | done | 1f7a844* |
| phase1-dogri-own-1791840638 | dogri | doi | own | 5.016 | 0 | 0.311 | 0.145 | 0.113 | 4852 |  | 969 | done | 1f7a844* |
| phase1-dogri-random-1791833301 | dogri |  | random | 0.262 | 0 | 0.713 | 0.369 | 0.561 | 4852 |  | 969 | done | 7f5ba89* |
| phase1-dogri-random-1791840731 | dogri |  | random | 0.262 | 0 | 0.425 | 0.187 | 0.181 | 4852 |  | 969 | done | 1f7a844* |
| phase1-dogri-random-1791834347 | dogri |  | random | 0.262 | 1 | 0.703 | 0.365 | 0.533 | 4852 |  | 969 | done | 7f5ba89* |
| phase1-dogri-random-1791840914 | dogri |  | random | 0.262 | 1 | 0.417 | 0.184 | 0.175 | 4852 |  | 969 | done | 1f7a844* |
| phase1-dogri-random-1791835402 | dogri |  | random | 0.262 | 2 | 0.717 | 0.369 | 0.564 | 4852 |  | 969 | done | 7f5ba89* |
| phase1-dogri-random-1791841096 | dogri |  | random | 0.262 | 2 | 0.415 | 0.183 | 0.170 | 4852 |  | 969 | done | 1f7a844* |
| phase1-dogri-random-1791836562 | dogri |  | random | 1.020 | 0 | 0.613 | 0.303 | 0.413 | 4852 |  | 969 | done | 7f5ba89* |
| phase1-dogri-random-1791841281 | dogri |  | random | 1.020 | 0 | 0.354 | 0.162 | 0.135 | 4852 |  | 969 | done | 1f7a844* |
| phase1-dogri-random-1791838198 | dogri |  | random | 1.020 | 1 | 0.612 | 0.302 | 0.411 | 4852 |  | 969 | done | 0a8bbf3* |
| phase1-dogri-random-1791841473 | dogri |  | random | 1.020 | 1 | 0.354 | 0.161 | 0.134 | 4852 |  | 969 | done | 1f7a844* |
| phase1-dogri-random-1791838850 | dogri |  | random | 1.020 | 2 | 0.613 | 0.303 | 0.415 | 4852 |  | 969 | done | a08bc1b* |
| phase1-dogri-random-1791841672 | dogri |  | random | 1.020 | 2 | 0.354 | 0.162 | 0.134 | 4852 |  | 969 | done | 1f7a844* |
| phase1-dogri-random-1791839668 | dogri |  | random | 5.016 | 0 | 0.548 | 0.262 | 0.331 | 4852 |  | 969 | done | 28e6dc8* |
| phase1-dogri-random-1791841891 | dogri |  | random | 5.016 | 0 | 0.334 | 0.153 | 0.127 | 4852 |  | 969 | done | 1f7a844* |
| phase1-dogri-random-1791839898 | dogri |  | random | 5.016 | 1 | 0.546 | 0.261 | 0.318 | 4852 |  | 969 | done | 28e6dc8* |
| phase1-dogri-random-1791842152 | dogri |  | random | 5.016 | 1 | 0.332 | 0.153 | 0.127 | 4852 |  | 969 | done | 1f7a844* |
| phase1-dogri-random-1791840126 | dogri |  | random | 5.016 | 2 | 0.552 | 0.263 | 0.318 | 4852 |  | 969 | done | 28e6dc8* |
| phase1-dogri-random-1791842391 | dogri |  | random | 5.016 | 2 | 0.332 | 0.153 | 0.132 | 4852 |  | 969 | done | 1f7a844* |

## Stage: step1-zero-shot

| run | target | donor | init | budget h | seed | WER | CER | tone CER | tone chars | CI | utts | status | commit |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| step1-zero-shot-dogri-zero-shot-head-as-1791849200 | dogri | as | zero-shot-head-as |  |  | 0.963 | 0.486 | 0.766 | 4852 |  | 969 | done | c473f74* |
| step1-zero-shot-dogri-zero-shot-head-bn-1791849209 | dogri | bn | zero-shot-head-bn |  |  | 0.903 | 0.454 | 0.761 | 4852 |  | 969 | done | c473f74* |
| step1-zero-shot-dogri-zero-shot-head-brx-1791849217 | dogri | brx | zero-shot-head-brx |  |  | 0.952 | 0.550 | 0.772 | 4852 |  | 969 | done | c473f74* |
| step1-zero-shot-dogri-zero-shot-head-doi-1791849228 | dogri | doi | zero-shot-head-doi |  |  | 0.311 | 0.145 | 0.113 | 4852 |  | 969 | done | c473f74* |
| step1-zero-shot-dogri-zero-shot-head-gu-1791849247 | dogri | gu | zero-shot-head-gu |  |  | 0.839 | 0.400 | 0.751 | 4852 |  | 969 | done | c473f74* |
| step1-zero-shot-dogri-zero-shot-head-hi-1791849257 | dogri | hi | zero-shot-head-hi |  |  | 0.759 | 0.338 | 0.654 | 4852 |  | 969 | done | c473f74* |
| step1-zero-shot-dogri-zero-shot-head-kn-1791849265 | dogri | kn | zero-shot-head-kn |  |  | 0.933 | 0.490 | 0.739 | 4852 |  | 969 | done | c473f74* |
| step1-zero-shot-dogri-zero-shot-head-kok-1791849237 | dogri | kok | zero-shot-head-kok |  |  | 0.826 | 0.402 | 0.788 | 4852 |  | 969 | done | c473f74* |
| step1-zero-shot-dogri-zero-shot-head-mai-1791849275 | dogri | mai | zero-shot-head-mai |  |  | 0.795 | 0.364 | 0.691 | 4852 |  | 969 | done | c473f74* |
| step1-zero-shot-dogri-zero-shot-head-ml-1791849284 | dogri | ml | zero-shot-head-ml |  |  | 0.955 | 0.561 | 0.846 | 4852 |  | 969 | done | c473f74* |
| step1-zero-shot-dogri-zero-shot-head-mr-1791849293 | dogri | mr | zero-shot-head-mr |  |  | 0.829 | 0.390 | 0.671 | 4852 |  | 969 | done | c473f74* |
| step1-zero-shot-dogri-zero-shot-head-ne-1791849303 | dogri | ne | zero-shot-head-ne |  |  | 0.874 | 0.426 | 0.706 | 4852 |  | 969 | done | c473f74* |
| step1-zero-shot-dogri-zero-shot-head-or-1791849313 | dogri | or | zero-shot-head-or |  |  | 0.903 | 0.460 | 0.735 | 4852 |  | 969 | done | c473f74* |
| step1-zero-shot-dogri-zero-shot-head-pa-1791849324 | dogri | pa | zero-shot-head-pa |  |  | 0.821 | 0.361 | 0.516 | 4852 |  | 969 | done | c473f74* |
| step1-zero-shot-dogri-zero-shot-head-sa-1791849332 | dogri | sa | zero-shot-head-sa |  |  | 0.882 | 0.447 | 0.774 | 4852 |  | 969 | done | c473f74* |
| step1-zero-shot-dogri-zero-shot-head-ta-1791849342 | dogri | ta | zero-shot-head-ta |  |  | 0.985 | 0.635 | 0.892 | 4852 |  | 969 | done | c473f74* |
| step1-zero-shot-dogri-zero-shot-head-te-1791849351 | dogri | te | zero-shot-head-te |  |  | 0.921 | 0.472 | 0.857 | 4852 |  | 969 | done | c473f74* |

`*` after a commit means the working tree had uncommitted changes when the run started.
