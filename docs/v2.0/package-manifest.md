# NRB 2.0.0 发布包与复现

实现提交：`735174612fe0fb298a83c872a0350f6eabf2d0a5`

评分器指纹：`7f2487673f1a214d60311193a369d48ab9215f9d7006554bf5c823e6ce5c7aa3`

23 个 ZIP，共 154,055,121 字节。20 题对应 21 个单条件题包，R06 A/B 分开交付；另有完整候选主包和独立评分器。主包由评测者保管，每次只分发所选单题目录。

## 复现

在该实现提交的 Git checkout 中，以 Python 3.12.14、zlib 1.3.2 执行：

```sh
python scripts/package_v2_release.py --seed 17 --out exports/reproduced-v2.0.0
```

输出目录必须是新目录。ZIP 使用固定时间戳、排序和文件权限。若使用其他压缩库版本，压缩字节可能变化；包内 MANIFEST.json 仍可逐文件核对内容。复现评分器 ZIP 时须使用上述实际 Git 提交，因为 RELEASE.json 记录 source_commit。

打包前核验了 137 个真实源文件，全部逐字节等于实现提交。其排序清单的 SHA-256 为 `9b31a8a5cfc35f0bef81ce85cbb6f95d0f5b2dc8538b7349299deface132720c`；完整清单见同目录 package-manifest.json。source_dirty=false 的程序定义仅检查 nrb_v1、nrb_v2；源文件清单核验另外覆盖实际材料、协议、环境、启动脚本和打包代码。

## 文件校验

下载入口由私有站点配置提供；本公开清单不存储新增的私有下载目的地。SHA-256 均指下面对应的本地发布 ZIP。

| 文件 | 字节 | SHA-256 |
|---|---:|---|
| NRB-v2.0.0-P01-candidate.zip | 3740 | `7f90dbebf2e947b975039887c7af6c71c6293f89ee67a7b4c4442172dc377ac6` |
| NRB-v2.0.0-P02-candidate.zip | 3847 | `fbac7dac4a34533a2f11b617803b7e0a7c8742c3799e277ae6b9f0d6240d93cc` |
| NRB-v2.0.0-P03-candidate.zip | 4151 | `d999d85769bfe254ae91099d81a95996250f2b43352ea20c57ab62058cfef790` |
| NRB-v2.0.0-P04-candidate.zip | 4467 | `607dba0267ab5b9d0703ba354857c836af0958418cbc562faa855992535793b1` |
| NRB-v2.0.0-P05-candidate.zip | 4709 | `85f4fd6489229e3bde9eaf727d0bb211a2afeb38bd6f974192f16c6db0471d9f` |
| NRB-v2.0.0-P06-candidate.zip | 4659 | `6dada90848ad2cf76ea17f2b78eda707fec8063c172f33408c301957fdec4f80` |
| NRB-v2.0.0-P07-candidate.zip | 4526 | `1e3b94bd142bcf46e43be33c97fd5ceccfb3002686523ec36e7c267f08a17c1b` |
| NRB-v2.0.0-P08-candidate.zip | 8170 | `a2fa70aa9dc6c621d34d35b82314a6714ce4db3d9623d5c873663130aa74307d` |
| NRB-v2.0.0-F01-candidate.zip | 5077 | `79340002f5cbe32d1750f5a80f5ee5b53d7e4d2dd8f3322cf27caaee559c9bbf` |
| NRB-v2.0.0-F02-candidate.zip | 4266 | `9fa4ae055757704084e9de032030476c5661c70b95b4a50f8ac2fc37208aa829` |
| NRB-v2.0.0-F03-candidate.zip | 4690 | `edabb8b621b10a89d0b80222a8b12f86264c929dad77e72adf1118b388f38cbe` |
| NRB-v2.0.0-L01-candidate.zip | 6852 | `4c9264bd2781f8b0a10d50d0ce54f1a2144f61f8669493affaf236c5cf7b5e31` |
| NRB-v2.0.0-R01-candidate.zip | 225199 | `99ea315ef775728f6ac258ac6e34abaeaf5694ebb1e688e72802a9e2496a02c5` |
| NRB-v2.0.0-R02-candidate.zip | 4614 | `ac33e332ed533edfc960b1497357e8384f0374c55d1bc5533091e9cc4244c61b` |
| NRB-v2.0.0-R03-candidate.zip | 5034 | `6995d4f5a2351135ed87531251695a8f33c17dda47cca105d5f60807be4d8afd` |
| NRB-v2.0.0-R04-candidate.zip | 124162 | `95355bf0b32e780e61be8df080831bbf6c384b6a687e8735eadebe78c3de48e4` |
| NRB-v2.0.0-R05-candidate.zip | 1067930 | `ee2bcf130d50f8e1ecfe764afab8599fcd9e8ecf74046bcc5677fa604985874f` |
| NRB-v2.0.0-R06-A-candidate.zip | 27511526 | `f6bf5e0df9fdbf68caa93cf93794b06a456d57a7e671b46e1d243026d729c5f7` |
| NRB-v2.0.0-R06-B-candidate.zip | 31447248 | `09846d8545fb39fd67534daeb5bcf92625b24e684b22e98d28d1065920b7a484` |
| NRB-v2.0.0-H01-candidate.zip | 5389 | `c299b95af2f75cc83c3b9c981f5fed47756f61c1980f5ded3376592c942c12d4` |
| NRB-v2.0.0-H02-candidate.zip | 3902 | `6ee9c23d2d07fbbe3263364c7cd8a32ca2b7cee9ff477b0e6910d5770c08db0d` |
| NRB-v2.0.0-all-candidates.zip | 60450997 | `729726a1b92d24b801ccf3c7453bfe8ff0bedde71db67dd5a8ddc0c45f390934` |
| NRB-v2.0.0-evaluator.zip | 33149966 | `a58b8d7fdb7037384d96fe2022cb9b4ef060a1b255e5921ef23e266529cebe99` |
