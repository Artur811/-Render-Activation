package com.ragestars.overlay;
import android.content.*;import android.security.keystore.*;import android.util.Base64;import java.nio.charset.StandardCharsets;import java.security.*;import java.util.UUID;import javax.crypto.*;import javax.crypto.spec.GCMParameterSpec;
final class LicenseStore {
 private static final String PREF="rs_license",ALIAS="RageStarsLicenseKey";private final SharedPreferences p;
 LicenseStore(Context c){p=c.getSharedPreferences(PREF,0);}
 String installationId(){String id=p.getString("installation_id",null);if(id==null){id=UUID.randomUUID().toString()+UUID.randomUUID();p.edit().putString("installation_id",id).apply();}return id;}
 private SecretKey key()throws Exception{KeyStore k=KeyStore.getInstance("AndroidKeyStore");k.load(null);if(k.containsAlias(ALIAS))return ((KeyStore.SecretKeyEntry)k.getEntry(ALIAS,null)).getSecretKey();KeyGenerator g=KeyGenerator.getInstance(KeyProperties.KEY_ALGORITHM_AES,"AndroidKeyStore");g.init(new KeyGenParameterSpec.Builder(ALIAS,KeyProperties.PURPOSE_ENCRYPT|KeyProperties.PURPOSE_DECRYPT).setBlockModes(KeyProperties.BLOCK_MODE_GCM).setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE).build());return g.generateKey();}
 void save(String id,String token)throws Exception{Cipher c=Cipher.getInstance("AES/GCM/NoPadding");c.init(Cipher.ENCRYPT_MODE,key());byte[] e=c.doFinal(token.getBytes(StandardCharsets.UTF_8));p.edit().putString("license_id",id).putString("token",Base64.encodeToString(e,2)).putString("iv",Base64.encodeToString(c.getIV(),2)).apply();}
 String token()throws Exception{String d=p.getString("token",null),iv=p.getString("iv",null);if(d==null||iv==null)return null;Cipher c=Cipher.getInstance("AES/GCM/NoPadding");c.init(Cipher.DECRYPT_MODE,key(),new GCMParameterSpec(128,Base64.decode(iv,2)));return new String(c.doFinal(Base64.decode(d,2)),StandardCharsets.UTF_8);}
 String licenseId(){return p.getString("license_id",null);}void clear(){p.edit().remove("token").remove("iv").remove("license_id").apply();}
}
