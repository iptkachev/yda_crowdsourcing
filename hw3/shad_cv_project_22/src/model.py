import torch
import torchvision.transforms as transforms
from torch.nn import functional as F
from torch import nn
from torch.nn import *
import pytorch_lightning as pl
import timm
from sklearn.metrics import f1_score
    
class ImageClassifier(pl.LightningModule):
    def __init__(self, trunk=None, class_weight=None, learning_rate=1e-3):
        super().__init__()
        self.class_weight = class_weight
        self.trunk = trunk or timm.create_model('mobilenetv2_100', pretrained=True, num_classes=2)
        self.learning_rate =  learning_rate

    def forward(self, x):
        return self.trunk(x)

    def predict_proba(self, x):
        probabilities = nn.functional.softmax(self.forward(x), dim=1)
        return probabilities

    def predict(self, x):
        return self.predict_class(self.forward(x))

    def predict_class(self, x):
        return torch.max(x, 1)[1]

    def configure_optimizers(self):
        optimizer = torch.optim.AdamW(self.parameters(),
                                      lr=self.learning_rate)
        return optimizer

    def training_step(self, batch, batch_idx):
        x, y = batch
        y_hat = self(x)
        loss = nn.CrossEntropyLoss(weight=self.class_weight)(y_hat, y)
        self.log("train_loss", loss)
        return loss

    def validation_step(self, batch, batch_idx):
        x, y = batch
        y_hat = self(x)
        loss = nn.CrossEntropyLoss(weight=self.class_weight)(y_hat, y)
        return y, self.predict_class(y_hat)

    def validation_epoch_end(self, outputs) -> None:
        y, y_hat = zip(*outputs)
        y, y_hat = torch.cat(y).numpy(), torch.cat(y_hat).numpy()
        self.log("val_f1_score", f1_score(y, y_hat, labels=1, average='binary'))