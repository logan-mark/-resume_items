#准备数据集
import torchvision
from torch.utils.data import DataLoader
from 深度学习入门学习.Model import *

train_data=torchvision.datasets.CIFAR10(root="./dataset",train=True,transform=torchvision.transforms.ToTensor,
                                        download=True)

test_data=torchvision.datasets.CIFAR10(root="./dataset",train=False,transform=torchvision.transforms.ToTensor,
                                       download=True)

#length长度
train_data_size=len(train_data)
test_data_size=len(train_data)
print("训练数据集的长度：{}".format(train_data_size))
print("测试集的长度为：{}".format(test_data_size))

#利用dataloader来加载数据集
train_dataloader=DataLoader(train_data,batch_size=64)
test_dataloader=DataLoader(test_data,batch_size=64)

#创建网络模型
pan=PAN()

#损失函数
loss_fn=nn.CrossEntropyLoss()

#优化器
learning_rate=0.01
learning_rate=1e-2

optimizer=torch.optim.SGD(pan.parameters(),lr=learning_rate)

#设置训练网络的参数，记录训练次数
total_train_step=0
#记录测试次数
total_test_step=0
#训练次数
epoch=10

for i in range(epoch):
    print("------第{}轮训练-------".format(i+1))

    #训练步骤开始
    for data in test_dataloader:
        imgs,targets=data
        outputs=pan(imgs)
        loss=loss_fn(outputs,targets)

        #优化器优化模型
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        total_train_step=total_test_step+1

        print("训练次数：{},loss:{}".format(total_train_step,loss.item()))

#测试步骤
total_test_loss=0
with torch.no_grad():
    for data in test_dataloader:
        imgs,targets=data
        output=pan(imgs)
        loss=loss_fn(outputs,targets)
        total_test_loss=total_test_loss+loss.item()

print("整体测试集上的loss：{}".format(total_test_loss))