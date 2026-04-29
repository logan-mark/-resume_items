from torch.utils.tensorboard import SummaryWriter
from torchvision import transforms
from PIL import Image

#tensor数据类型
#这里是相对路径
img_path= "hymenoptera_data/train/ants_image/0013035.jpg"
img=Image.open(img_path)

writer=SummaryWriter("logs")


tensor_trans=transforms.ToTensor()
tensor_img=tensor_trans(img)

writer.add_image("Tensor_img",tensor_img)

writer.close()