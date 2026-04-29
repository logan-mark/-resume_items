from torch.utils.tensorboard import SummaryWriter
import numpy as np
from PIL import Image
writer=SummaryWriter("logs")
image_path= "hymenoptera_data/train/ants_image/0013035.jpg"
image_PIL=Image.open(image_path)
image_array=np.array(image_PIL)
print(type(image_array))
print(image_array.shape)
writer.add_image("test",image_array,1,dataformats='HWC')
for i in range(100):

    writer.add_scalar("y=2x",3*i,i)

writer.close()