import torch
from torch import nn



class PPNN(nn.Module):
    def __init__(self):
        super().__init__()

    def forward(self,input ):
        output=input+1
        return output



ppnn=PPNN()
x=torch.tensor(1.0)
output=ppnn(x)
print(output)