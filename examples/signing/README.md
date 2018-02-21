How to create a new signing key and sign APKs in different ways:

1) Request a new certificate:
```
$ openssl req -newkey rsa:2048 -nodes -keyout key.pem -x509 -days 36500 -out certificate.pem
```

2) convert key to PKCS#8 in DER encoding and convert the certificate to DER as
well, for further testing:
```
$ openssl pkcs8 -topk8 -inform PEM -outform DER -in key.pem -out priv.key -nocrypt
$ openssl x509 -inform pem -outform der -in certificate.pem -out certificate.der
```

3) delete unused file
```
$ rm key.pem
```

4) Use APK Signer:
```
$ apksigner sign --key priv.key --cert certificate.pem --v1-signing-enabled --v2-signing-enabled --v1-signer-name ANDROGUARD TestActivity_unsigned.apk
```

5) Verify that the file is signed:
```
$ apksigner verify --verbose TestActivity_unsigned.apk
Verifies
Verified using v1 scheme (JAR signing): true
Verified using v2 scheme (APK Signature Scheme v2): true
Number of signers: 1
```

