import numpy as np

def _window(image, radius, mode="reflect"):
    padded = np.pad(image, ((radius, radius), (radius, radius), (0, 0)), mode=mode)
    h, w, c = image.shape
    return [padded[y:y+h, x:x+w] for y in range(2*radius+1) for x in range(2*radius+1)]

def median_filter(image, radius=1):
    if radius < 1:
        return image.copy()
    windows = _window(image, radius)
    return np.median(np.stack(windows), axis=0).astype(np.uint8)

def minimum_filter(image, radius=1):
    return np.min(np.stack(_window(image, radius)), axis=0).astype(np.uint8)

def maximum_filter(image, radius=1):
    return np.max(np.stack(_window(image, radius)), axis=0).astype(np.uint8)

def rank_filter(image, radius=1, percentile=50):
    windows = np.stack(_window(image, radius))
    return np.percentile(windows, percentile, axis=0).astype(np.uint8)

def linear_contrast(image):
    result = image.astype(np.float32)
    out = np.empty_like(image)
    for channel in range(image.shape[2]):
        low, high = result[:,:,channel].min(), result[:,:,channel].max()
        if high == low:
            out[:,:,channel] = image[:,:,channel]
        else:
            out[:,:,channel] = np.clip((result[:,:,channel]-low)*255/(high-low),0,255)
    return out.astype(np.uint8)

def histogram_equalization_rgb(image):
    out = np.empty_like(image)
    for c in range(image.shape[2]):
        hist = np.bincount(image[:,:,c].ravel(), minlength=256)
        cdf = hist.cumsum()
        nonzero = cdf[cdf > 0]
        cdf_min = nonzero[0] if len(nonzero) else 0
        denom = image.shape[0]*image.shape[1]-cdf_min
        lut = np.zeros(256,dtype=np.uint8) if denom <= 0 else np.clip((cdf-cdf_min)*255/denom,0,255).astype(np.uint8)
        out[:,:,c] = lut[image[:,:,c]]
    return out

def histogram_equalization_value(image):
    hsv = rgb_to_hsv(image)
    hsv[:,:,2] = equalize_channel(hsv[:,:,2])
    return hsv_to_rgb(hsv)

def equalize_channel(channel):
    hist=np.bincount(channel.ravel(),minlength=256)
    cdf=hist.cumsum()
    nz=cdf[cdf>0]
    cmin=nz[0] if len(nz) else 0
    denom=channel.size-cmin
    if denom<=0: return channel.copy()
    lut=np.clip((cdf-cmin)*255/denom,0,255).astype(np.uint8)
    return lut[channel]

def rgb_to_hsv(rgb):
    a=rgb.astype(np.float32)/255
    mx=a.max(axis=2); mn=a.min(axis=2); d=mx-mn
    h=np.zeros_like(mx); s=np.zeros_like(mx); v=mx
    mask=d!=0
    s[mask]=d[mask]/mx[mask]
    r,g,b=a[:,:,0],a[:,:,1],a[:,:,2]
    m=(mx==r)&mask; h[m]=((g[m]-b[m])/d[m])%6
    m=(mx==g)&mask; h[m]=(b[m]-r[m])/d[m]+2
    m=(mx==b)&mask; h[m]=(r[m]-g[m])/d[m]+4
    h=h/6
    return np.stack([h,s,v],axis=2)

def hsv_to_rgb(hsv):
    h,s,v=hsv[:,:,0],hsv[:,:,1],hsv[:,:,2]
    k=np.floor(h*6).astype(int); f=h*6-k
    p=v*(1-s); q=v*(1-f*s); t=v*(1-(1-f)*s)
    choices=np.stack([np.stack([v,t,p],2),np.stack([q,v,p],2),np.stack([p,v,t],2),np.stack([p,q,v],2),np.stack([t,p,v],2),np.stack([v,p,q],2)])
    out=np.empty_like(hsv)
    for i in range(6):
        mask=(k%6)==i
        out[mask]=choices[i][mask]
    return np.clip(out*255,0,255).astype(np.uint8)
